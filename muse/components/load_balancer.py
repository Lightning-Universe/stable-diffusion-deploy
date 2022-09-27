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
from muse.CONST import REQUEST_TIMEOUT


@dataclass
class FastAPIBuildConfig(L.BuildConfig):
    requirements = ["fastapi==0.78.0", "uvicorn==0.17.6"]


class LoadBalancer(L.LightningWork):
    """Forward the requests to Model inference servers in Round Robin fashion and implements automatic batching."""

    def __init__(self, max_batch_size=8, max_wait_time=10, **kwargs):
        super().__init__(cloud_compute=L.CloudCompute("cpu-medium"), cloud_build_config=FastAPIBuildConfig(), **kwargs)
        self._server_ready = False
        self.servers = []
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
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
                    len(batch) >= self.max_batch_size or (time.time() - self._last_batch_sent) > self.max_wait_time
                ):
                    has_sent = True

                    asyncio.create_task(self.send_batch(batch))

                    self._batch[quality] = self._batch[quality][self.max_batch_size :]
                    batch = self._batch[quality][: self.max_batch_size]

            if has_sent:
                self._last_batch_sent = time.time()

    def run(self, servers: List[str]):
        self.servers = servers
        if self._server_ready:
            return

        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        print(self.servers)

        self._ITER = cycle(self.servers)
        self._last_batch_sent = time.time()

        app = FastAPI()

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
            return len(asyncio.all_tasks(loop=None)) - 4

        @app.put("/system/update-servers")
        async def update_servers(servers: List[str]):
            self.servers = servers
            self._ITER = cycle(self.servers)

        async def process_request(data: Data):
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
                    if isinstance(result, HTTPException):
                        raise result
                    elif isinstance(result, Exception):
                        raise HTTPException(500, result.args[0])
                    return result

        @app.post("/api/surprise-me")
        async def surprise_me():
            data = Data(dream=random_prompt())
            return await process_request(data)

        @app.post("/api/predict")
        async def balance_api(data: Data):
            if data.dream.lower() == "surprise me":
                data.dream = random_prompt()
            return await process_request(data)

        uvicorn.run(app, host=self.host, port=self.port, loop="uvloop", access_log=False)

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
