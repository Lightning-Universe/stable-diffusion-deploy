import asyncio
import json
import time
import uuid
from dataclasses import dataclass
from http.client import HTTPException
from itertools import cycle
from threading import Lock, Thread
from typing import List

import lightning as L
import requests

from dream.components.utils import Data


@dataclass
class FastAPIBuildConfig(L.BuildConfig):
    requirements = ["fastapi==0.78.0", "uvicorn==0.17.6"]


class LoadBalancer(L.LightningWork):
    def __init__(self, max_batch_size=4, max_wait_time=5, **kwargs):
        super().__init__(cloud_build_config=FastAPIBuildConfig(), **kwargs)
        self.servers = []
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self._ITER = None
        self._batch = {"high": [], "low": []}
        self._batch_lock = None
        self._responses = {}  # {request_id: response}
        self._last_batch_sent = 0

    def send_batches(self):
        while True:
            time.sleep(1)

            has_sent = False

            # Naive shutdown signal
            if self._batch is None:
                return

            for quality in self._batch.keys():
                batch = self._batch[quality][: self.max_batch_size]
                while batch and (
                    len(batch) >= self.max_batch_size or time.time() - self._last_batch_sent > self.max_wait_time
                ):
                    print("Sending batch")
                    has_sent = True

                    with self._batch_lock:
                        self._batch[quality] = self._batch[quality][self.max_batch_size :]

                    server = next(self._ITER)

                    # TODO: This probably doesn't need to use async
                    # TODO: This timeout is irrelevant as running in a thread
                    data = {"batch": [b[1] for b in batch]}
                    result = requests.post(f"{server}/api/predict", data=json.dumps(data))
                    result.raise_for_status()
                    result = result.json()
                    result = {request[0]: r for request, r in zip(batch, result)}
                    print(result)
                    self._responses.update(result)

                    batch = self._batch[quality][: self.max_batch_size]

            if has_sent:
                self._last_batch_sent = time.time()

    def run(self, servers: List[str]):
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        self.servers = servers
        print(self.servers)

        self._ITER = cycle(self.servers)
        self._batch_lock = Lock()
        self._last_batch_sent = time.time()

        app = FastAPI()

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        app.REQUEST_THREAD: Thread = None

        @app.on_event("startup")
        def startup_event():
            app.REQUEST_THREAD = Thread(target=self.send_batches)
            app.REQUEST_THREAD.start()

        @app.on_event("shutdown")
        def shutdown_event():
            self._batch = None
            app.REQUEST_THREAD.join()

        @app.post("/api/predict")
        async def balance_api(data: Data):
            """"""
            if not self.servers:
                raise HTTPException(500, "None of the workers are healthy!")

            request_id = uuid.uuid4().hex
            request = (request_id, data.dict())
            with self._batch_lock:
                self._batch["high" if data.high_quality else "low"].append(request)

            while True:
                await asyncio.sleep(1)

                if request_id in self._responses:
                    result = self._responses[request_id]
                    del self._responses[request_id]
                    return result

        uvicorn.run(app, host=self.host, port=self.port)

    def update_servers(self, servers: List[str]):
        self.servers = servers
        self._ITER = cycle(self.servers)
