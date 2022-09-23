import asyncio
import time
import uuid
from dataclasses import dataclass
from http.client import HTTPException
from itertools import cycle
from threading import Thread
from typing import TYPE_CHECKING, Dict, List

import aiohttp
import lightning as L
import requests

from dream import StableDiffusionServe
from dream.components.utils import Data, TimeoutException
from dream.CONST import REQUEST_TIMEOUT

if TYPE_CHECKING:
    from dream import StableDiffusionServe


@dataclass
class FastAPIBuildConfig(L.BuildConfig):
    requirements = ["fastapi==0.78.0", "uvicorn==0.17.6"]


class Scheduler:
    """Simple round-robin scheduling for servers."""

    def __init__(self, servers: List[str]):
        self.servers = servers
        self._iter = cycle(self.servers)

    def update_server(self, server_works: List["StableDiffusionServe"]):
        old_servers = set(self.servers)
        self.servers = [server.url for server in server_works if server.url]
        new_servers = set(self.servers)
        print("servers added:", new_servers - old_servers)
        self._iter = cycle(self.servers)

    def get_server(self):
        return next(self._iter)


class LeastConnectionScheduler(Scheduler):
    def __init__(self, servers: List[str], update_interval: int = 5):
        super().__init__(servers=servers)
        self.update_interval = update_interval  # seconds
        self.server_backlogs: Dict[str, int] = {server: 0 for server in servers}
        Thread(target=self.run_in_background, daemon=True).start()

    def update_server(self, server_works: List["StableDiffusionServe"]):
        super().update_server(server_works)
        self.server_backlogs = {}
        self.update_backlog()

    def update_backlog(self) -> None:
        for server in self.servers:
            resp = requests.get(f"{server}/system/backlog", timeout=self.update_interval)
            resp.raise_for_status()
            self.server_backlogs[server] = int(resp.json())

    def run_in_background(self):
        last_updated = time.time()
        while True:
            if time.time() - last_updated > self.update_interval:
                self.update_backlog()
                last_updated = time.time()

    def get_server(self) -> str:
        urls = sorted(self.server_backlogs.items(), key=lambda x: x[1])[0]
        print(urls)
        return urls[0]


class LoadBalancer(L.LightningWork):
    """Forward the requests to Model inference servers in Round Robin fashion and implements automatic batching."""

    def __init__(self, max_batch_size=8, max_wait_time=10, **kwargs):
        super().__init__(cloud_build_config=FastAPIBuildConfig(), **kwargs)
        self._scheduler: Scheduler = None
        self._server_ready = False
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self._batch = {"high": [], "low": []}
        self._responses = {}  # {request_id: response}
        self._last_batch_sent = 0

    async def send_batch(self, batch):
        server = self._scheduler.get_server()
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
        self._scheduler = LeastConnectionScheduler(servers)
        if self._server_ready:
            return

        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        print(self._scheduler.servers)

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

        @app.post("/api/predict")
        async def balance_api(data: Data):
            """"""
            if not self._scheduler.servers:
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

        uvicorn.run(app, host=self.host, port=self.port, loop="uvloop", access_log=False)

    def update_servers(self, servers: List["StableDiffusionServe"]):
        self._scheduler.update_server(servers)
