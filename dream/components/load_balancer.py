import asyncio
from dataclasses import dataclass
from http.client import HTTPException
from itertools import cycle
from typing import List

import aiohttp
import lightning as L

from dream.components.utils import Data, TimeoutException
from dream.CONST import REQUEST_TIMEOUT


@dataclass
class FastAPIBuildConfig(L.BuildConfig):
    requirements = ["fastapi==0.78.0", "uvicorn==0.17.6"]


class LoadBalancer(L.LightningWork):
    def __init__(self, **kwargs):
        super().__init__(cloud_build_config=FastAPIBuildConfig(), **kwargs)
        self.servers = []
        self._ITER = None

    def run(self, servers: List[str]):
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        self.servers = servers
        print(self.servers)

        self._ITER = cycle(self.servers)

        app = FastAPI()

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.post("/api/predict")
        async def balance_api(data: Data):
            """"""
            if not self.servers:
                raise HTTPException(500, "None of the workers are healthy!")
            server = next(self._ITER)
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{server}/api/predict", json=data.dict(), timeout=REQUEST_TIMEOUT
                    ) as result:
                        if result.status == 408:
                            raise TimeoutException()
                        result.raise_for_status()
                        return await result.json()
            except asyncio.TimeoutError:
                raise TimeoutException()

        uvicorn.run(app, host=self.host, port=self.port)

    def update_servers(self, servers: List[str]):
        self.servers = servers
        self._ITER = cycle(self.servers)
