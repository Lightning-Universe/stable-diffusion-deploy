import asyncio
import time
import uuid
from dataclasses import dataclass
from itertools import cycle
from typing import List

import aiohttp
import lightning as L
import requests
from fastapi import HTTPException

from muse.components.utils import Data, SysInfo, TimeoutException, random_prompt
from muse.CONST import KEEP_ALIVE_TIMEOUT, PREDICT_RATE_LIMIT, REQUEST_TIMEOUT


@dataclass
class FastAPIBuildConfig(L.BuildConfig):
    requirements = ["fastapi==0.78.0", "uvicorn==0.17.6"]


class LoadBalancer(L.LightningWork):
    r"""The LoadBalancer is a LightningWork component that collects the requests and sends it to the prediciton API
    asynchronously using RoundRobin scheduling. It also performs auto batching of the incoming requests.

    Args:
        max_batch_size: Number of requests processed at once.
        batch_timeout_secs: Number of seconds to wait before sending the requests to process.
        \**kwargs: Arguments passed to :func:`LightningWork.init` like ``CloudCompute``, ``BuildConfig``, etc.
    """

    def __init__(self, max_batch_size=8, batch_timeout_secs=10, **kwargs):
        super().__init__(cloud_compute=L.CloudCompute("cpu-medium"), cloud_build_config=FastAPIBuildConfig(), **kwargs)
        self._server_ready = False
        self.servers = []
        self.max_batch_size = max_batch_size
        self.batch_timeout_secs = batch_timeout_secs
        self._ITER = None
        self._batch = {"high": [], "low": []}
        self._responses = {}  # {request_id: response}
        self._last_batch_sent = 0

    async def send_batch(self, batch):
        server = next(self._ITER)
        data = {"batch": [b[1] for b in batch]}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{server}/api/predict", json=data, timeout=REQUEST_TIMEOUT) as result:
                    if result.status == 408:
                        raise TimeoutException()
                    result.raise_for_status()
                    result = await result.json()
                    result = {request[0]: r for request, r in zip(batch, result)}
                    self._responses.update(result)
        except Exception as e:
            result = {request[0]: e for request in batch}
            self._responses.update(result)

    async def consumer(self):
        while True:
            await asyncio.sleep(0.1)

            has_sent = False

            for quality in self._batch.keys():
                batch = self._batch[quality][: self.max_batch_size]
                while batch and (
                    (len(batch) >= self.max_batch_size)
                    or ((time.time() - self._last_batch_sent) > self.batch_timeout_secs)
                ):
                    has_sent = True

                    asyncio.create_task(self.send_batch(batch))

                    self._batch[quality] = self._batch[quality][self.max_batch_size :]
                    batch = self._batch[quality][: self.max_batch_size]

            if has_sent:
                self._last_batch_sent = time.time()

    async def process_request(self, data: Data):
        if not self.servers:
            raise HTTPException(500, "None of the workers are healthy!")

        request_id = uuid.uuid4().hex
        request = (request_id, data.dict())
        self._batch["high" if data.high_quality else "low"].append(request)

        while True:
            await asyncio.sleep(0.1)

            if request_id in self._responses:
                result = self._responses[request_id]
                del self._responses[request_id]
                if isinstance(result, Exception):
                    raise HTTPException(500, result.args[0])
                elif isinstance(result, HTTPException):
                    raise result
                return result

    def run(self, servers: List[str]):
        self.servers = servers
        if self._server_ready:
            return

        self.start_fastapi_app()

    def start_fastapi_app(self):

        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.requests import Request
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.errors import RateLimitExceeded
        from slowapi.util import get_remote_address

        print(self.servers)

        self._ITER = cycle(self.servers)
        self._last_batch_sent = time.time()

        limiter = Limiter(key_func=get_remote_address)
        app = FastAPI()
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

        app.SEND_TASK = None

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.on_event("startup")
        async def startup_event():
            app.SEND_TASK = asyncio.create_task(self.consumer())
            self._server_ready = True

        @app.on_event("shutdown")
        def shutdown_event():
            app.SEND_TASK.cancel()
            self._server_ready = False

        @app.get("/system/info", response_model=SysInfo)
        async def sys_info():
            return SysInfo(
                num_workers=len(self.servers), servers=self.servers, num_requests=len(asyncio.all_tasks()) - 4
            )

        @app.get("/num-requests")
        async def num_requests():
            # TODO: improve the hard coded logic
            return len(asyncio.all_tasks(loop=None)) - 4

        @app.put("/system/update-servers")
        async def update_servers(servers: List[str]):
            self.servers = servers
            self._ITER = cycle(self.servers)

        @app.post("/api/surprise-me")
        @limiter.limit("10/minute")
        async def surprise_me(request: Request):
            data = Data(dream=random_prompt())
            return await self.process_request(data)

        @app.post("/api/predict")
        @limiter.limit(PREDICT_RATE_LIMIT)
        async def balance_api(data: Data, request: Request):
            if data.dream.lower() == "surprise me":
                data.dream = random_prompt()
            return await self.process_request(data)

        uvicorn.run(
            app, host=self.host, port=self.port, loop="uvloop", timeout_keep_alive=KEEP_ALIVE_TIMEOUT, access_log=False
        )

    def update_servers(self, server_works: List[L.LightningWork]):
        old_servers = set(self.servers)
        self.servers = [server.url for server in server_works if server.url]
        new_servers = set(self.servers)
        if new_servers - old_servers:
            print("servers added:", new_servers - old_servers)

        deleted_servers = old_servers - new_servers
        if deleted_servers:
            print("deleted servers:", deleted_servers)

        servers = list(new_servers)
        headers = {
            "accept": "application/json",
        }
        requests.put(f"{self.url}/system/update-servers", json=servers, headers=headers, timeout=10)
