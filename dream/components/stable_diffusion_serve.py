import base64
import importlib
import os.path
import signal
import tarfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from io import BytesIO
from os import get_terminal_size
from pathlib import Path
from typing import List

import lightning as L
import numpy as np
import torch
from PIL import Image
from torch import autocast

from dream.components.utils import Data, DataBatch, TimeoutException, exit_threads
from dream.CONST import IMAGE_SIZE, REQUEST_TIMEOUT


@dataclass
class FastAPIBuildConfig(L.BuildConfig):
    requirements = ["fastapi==0.78.0", "uvicorn==0.17.6"]


class StableDiffusionServe(L.LightningWork):
    """Deploys the Stable Diffusion model with FastAPI.

    tolerable_failures: total number of failures after which the worker status becomes unhealthy.
    """

    def __init__(self, tolerable_failures=2, **kwargs):
        super().__init__(cloud_build_config=FastAPIBuildConfig(), **kwargs)
        self.num_failures = 0
        self._model = None
        self.tolerable_failures = tolerable_failures

    @staticmethod
    def download_weights(url: str, target_folder: str):
        dest = target_folder / f"{os.path.basename(url)}"
        if not os.path.exists(dest):
            urllib.request.urlretrieve(url, dest)

    def build_model(self):
        """The `build_model(...)` method returns a model and the returned model is set to `self._model` state."""

        import os

        import torch
        from omegaconf import OmegaConf

        print("loading model...")
        if torch.cuda.is_available() or True:
            device = torch.device("cuda")
            weights_folder = Path("resources/stable-diffusion-v1-4")
            os.makedirs(weights_folder, exist_ok=True)

            print("Downloading weights...")
            self.download_weights(
                "https://pl-public-data.s3.amazonaws.com/dream_stable_diffusion/sd_amp_traced.pt",
                weights_folder,
            )
            sd_fused = torch.jit.load(weights_folder / "sd_amp_traced.pt")
            sd_fused = sd_fused.to(device)
            config = OmegaConf.load("config.yaml")
            model = instantiate_from_config(config.model)

            model.apply_model = lambda x, t, c: sd_fused(_x=x, _t=t, _cnd=c)
            # delete the original model
            del model.model  # lol
            model = model.to(device)
            torch.cuda.empty_cache()

            # warmup
            c, uc = get_texttensors(model, ["warm up machine"] * 3)
            model.sample_log(
                cond=c,
                batch_size=3,
                ddim=True,
                ddim_steps=2,
                unconditional_guidance_scale=5.0,
                unconditional_conditioning=uc,
            )

            torch.cuda.empty_cache()
            print("model loaded")
        else:
            model = None
            print("model set to None")
        return model

    @torch.inference_mode()
    def predict(self, dreams: List[Data], entry_time: int):
        if time.time() - entry_time > REQUEST_TIMEOUT:
            raise TimeoutException()

        height = width = IMAGE_SIZE
        num_inference_steps = 50 if dreams[0].high_quality else 25

        prompts = [dream.dream for dream in dreams]
        with autocast("cuda"):
            if torch.cuda.is_available() or True:
                torch.cuda.empty_cache()
                c, uc = get_texttensors(self._model, prompts)
                sample_scaled, _ = self._model.sample_log(
                    cond=c,
                    batch_size=len(prompts),
                    ddim=True,
                    ddim_steps=num_inference_steps,
                    unconditional_guidance_scale=5.0,
                    unconditional_conditioning=uc,
                )

                images = self._model.decode_first_stage(sample_scaled)
                images = images.permute(0, 2, 3, 1) * 255.0
                images = images.cpu().numpy()
                pil_results = [Image.fromarray(img.astype(np.uint8)) for img in images]
            else:
                pil_results = [Image.fromarray(np.random.randint(0, 255, (height, width, 3), dtype="uint8"))] * len(
                    prompts
                )

        results = []
        for image in pil_results:
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            results.append(f"data:image/png;base64,{img_str}")

        return results

    @property
    def health_status(self):
        return self.num_failures < self.tolerable_failures

    def run(self):
        import subprocess

        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        subprocess.run("nvidia-smi", shell=True)

        if self._model is None:
            self._model = self.build_model()

        self._fastapi_app = app = FastAPI()
        app.POOL: ThreadPoolExecutor = None

        @app.on_event("startup")
        def startup_event():
            app.POOL = ThreadPoolExecutor(max_workers=1)

        @app.on_event("shutdown")
        def shutdown_event():
            app.POOL.shutdown(wait=False)

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/api/health")
        def health():
            return self.health_status

        @app.post("/api/predict")
        def predict_api(data: DataBatch):
            """Dream a dream. Defines the REST API which takes the text prompt, number of images and image size in the
            request body.

            This API returns an image generated by the model in base64 format.
            """
            try:
                entry_time = time.time()
                print(f"request: {data}")
                result = app.POOL.submit(
                    self.predict,
                    data.batch,
                    entry_time=entry_time,
                ).result(timeout=REQUEST_TIMEOUT)
                return result
            except (TimeoutError, TimeoutException):
                # hack: once there is a timeout then all requests after that is getting timedout
                # old_pool = app.POOL
                # app.POOL = ThreadPoolExecutor(max_workers=1)
                # old_pool.shutdown(wait=False)
                # signal.signal(signal.SIGINT, lambda sig, frame: exit_threads(old_pool))
                self.num_failures += 1
                raise TimeoutException()

        uvicorn.run(app, host=self.host, port=self.port, timeout_keep_alive=30)


def get_texttensors(model, prompts):
    c = model.get_learned_conditioning(prompts)
    uc = model.get_learned_conditioning(len(c) * [""])
    return c, uc


def instantiate_from_config(config):
    if not "target" in config:
        if config == "__is_first_stage__":
            return None
        elif config == "__is_unconditional__":
            return None
        raise KeyError("Expected key `target` to instantiate.")
    return get_obj_from_str(config["target"])(**config.get("params", dict()))


def get_obj_from_str(string, reload=False):
    module, cls = string.rsplit(".", 1)
    if reload:
        module_imp = importlib.import_module(module)
        importlib.reload(module_imp)
    return getattr(importlib.import_module(module, package=None), cls)
