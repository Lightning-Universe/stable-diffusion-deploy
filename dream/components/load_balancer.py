import asyncio
import time
import uuid
from dataclasses import dataclass
from http.client import HTTPException
from itertools import cycle
from typing import List

import aiohttp
import lightning as L

from dream.components.utils import Data, TimeoutException, random_prompt
from dream.CONST import REQUEST_TIMEOUT


@dataclass
class FastAPIBuildConfig(L.BuildConfig):
    requirements = ["fastapi==0.78.0", "uvicorn==0.17.6"]


class LoadBalancer(L.LightningWork):
    """Forward the requests to Model inference servers in Round Robin fashion and implements automatic batching."""

    def __init__(self, max_batch_size=8, max_wait_time=10, **kwargs):
        super().__init__(cloud_build_config=FastAPIBuildConfig(), **kwargs)
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

    async def send_batches(self):
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
            app.SEND_TASK = asyncio.create_task(self.send_batches())
            self._server_ready = True

        @app.on_event("shutdown")
        def shutdown_event():
            app.SEND_TASK.cancel()
            self._server_ready = False

        @app.get("/num-requests")
        async def num_requests():
            return len(asyncio.all_tasks(loop=None)) - 4

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
                    if isinstance(result, (Exception, HTTPException)):
                        raise result
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

    def update_servers(self, servers: List[L.LightningWork]):
        old_servers = set(self.servers)
        self.servers = [server.url for server in servers if server.url]
        new_servers = set(self.servers)
        print("servers added:", new_servers - old_servers)
        self._ITER = cycle(self.servers)
