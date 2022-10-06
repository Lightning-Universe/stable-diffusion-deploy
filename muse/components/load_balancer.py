import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from itertools import cycle
from typing import List

import aiohttp
import lightning as L
import requests
from fastapi import HTTPException
from fastapi.requests import Request
from lightning.app.storage import Drive

from muse.CONST import INFERENCE_REQUEST_TIMEOUT, KEEP_ALIVE_TIMEOUT, SENTRY_API_KEY
from muse.utility.data_io import Data, SysInfo, TimeoutException, random_prompt
from muse.utility.exception_handling import raise_granular_exception
from muse.utility.rate_limiter import RULES, auth_function


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
        self.db_drive = Drive("lit://muse_db")

    async def send_batch(self, batch):
        server = next(self._ITER)
        data = {"batch": [b[1] for b in batch]}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{server}/api/predict", json=data, timeout=INFERENCE_REQUEST_TIMEOUT
                ) as result:
                    if result.status == 408:
                        raise TimeoutException()
                    result.raise_for_status()
                    result = await result.json()
                    result = {request[0]: r for request, r in zip(batch, result)}
                    self._responses.update(result)
        except Exception as e:
            logging.exception(e)
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
                    or ((time.time() - self._last_batch_sent) > self.batch_timeout_secs)  # noqa: W503
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
                raise_granular_exception(result)
                return result

    def run(self, servers: List[str]):
        if self._server_ready or not servers:
            return

        self.servers = servers
        self.start_fastapi_app()

    def start_fastapi_app(self):  # noqa: C901

        import sentry_sdk
        import uvicorn
        from fastapi import FastAPI, Header
        from fastapi.middleware.cors import CORSMiddleware
        from ratelimit import RateLimitMiddleware
        from ratelimit.backends.simple import MemoryBackend
        from sqlmodel import Session
        from starlette_exporter import PrometheusMiddleware, handle_metrics

        from muse.db.backend import create_db_and_tables, engine, sqlite_file_name
        from muse.db.models import RequestMonitor

        print(self.servers)

        self._ITER = cycle(self.servers)
        self._last_batch_sent = time.time()

        app = FastAPI()
        app.request_count = 0

        if SENTRY_API_KEY:
            print("enabled sentry monitoring")
            sentry_sdk.init(
                dsn=SENTRY_API_KEY,
                # Set traces_sample_rate to 1.0 to capture 100%
                # of transactions for performance monitoring.
                # We recommend adjusting this value in production,
                traces_sample_rate=1.0,
            )

        app.num_current_requests = 0
        app.last_process_time = 0
        app.SEND_TASK = None

        @app.middleware("http")
        async def current_request_counter(request: Request, call_next):
            if not request.scope["path"] == "/api/predict":
                return await call_next(request)
            app.num_current_requests += 1
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            app.last_process_time = process_time
            app.num_current_requests -= 1
            return response

        app.add_middleware(PrometheusMiddleware, app_name="load_balancer", prefix="muse")
        app.add_route("/metrics", handle_metrics)

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        app.add_middleware(
            RateLimitMiddleware,
            authenticate=auth_function,
            backend=MemoryBackend(),
            config={
                r"^/api/predict": RULES,
            },
        )

        @app.on_event("startup")
        async def startup_event():
            if "muse.db" in self.db_drive.list():
                logging.info("loading DB from Drive")
                self.db_drive.get(sqlite_file_name, overwrite=True)
            app.SEND_TASK = asyncio.create_task(self.consumer())
            create_db_and_tables()
            self._server_ready = True

        @app.on_event("shutdown")
        def shutdown_event():
            self.db_drive.put(sqlite_file_name)
            app.SEND_TASK.cancel()
            self._server_ready = False

        @app.get("/system/info", response_model=SysInfo)
        async def sys_info():
            return SysInfo(
                num_workers=len(self.servers),
                servers=self.servers,
                num_requests=app.num_current_requests,
                process_time=app.last_process_time,
            )

        @app.get("/num-requests")
        async def num_requests() -> int:
            return app.num_current_requests

        @app.put("/system/update-servers")
        async def update_servers(servers: List[str]):
            self.servers = servers
            self._ITER = cycle(self.servers)

        @app.post("/api/surprise-me")
        async def surprise_me():
            data = Data(dream=random_prompt())
            return await self.process_request(data)

        @app.post("/api/predict")
        async def balance_api(data: Data, x_api_key: str = Header(default=None)):
            with Session(engine) as session:
                start_time = time.perf_counter()

                if data.dream.lower() == "surprise me":
                    data.dream = random_prompt()
                result = await self.process_request(data)

                process_time = time.perf_counter() - start_time
                app.request_count += 1
                request_monitor = RequestMonitor(
                    prompt=data.dream,
                    request_count=app.request_count,
                    model_server_process_time=-1,  # TODO: fetch worker server time
                    load_balancer_process_time=process_time,
                )
                session.add(request_monitor)
                session.commit()

            if app.request_count % 10 == 0:
                logging.info("refreshing db drive")
                self.db_drive.put(sqlite_file_name)
            return result

        uvicorn.run(
            app, host=self.host, port=self.port, loop="uvloop", timeout_keep_alive=KEEP_ALIVE_TIMEOUT, access_log=False
        )

    def update_servers(self, server_works: List[L.LightningWork]):
        old_servers = set(self.servers)
        self.servers: List[str] = [server.url for server in server_works if server.url]
        new_servers = set(self.servers)
        if new_servers == old_servers:
            return
        if new_servers - old_servers:
            print("servers added:", new_servers - old_servers)

        deleted_servers = old_servers - new_servers
        if deleted_servers:
            print("deleted servers:", deleted_servers)

        servers = self.servers
        headers = {
            "accept": "application/json",
        }
        requests.put(f"{self.url}/system/update-servers", json=servers, headers=headers, timeout=10)
