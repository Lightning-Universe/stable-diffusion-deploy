import base64
import os.path
import signal
import tarfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from io import BytesIO
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
        dest = target_folder + f"/{os.path.basename(url)}"
        urllib.request.urlretrieve(url, dest)
        file = tarfile.open(dest)

        # extracting file
        file.extractall(target_folder)
    
    @staticmethod
    @torch.no_grad()
    def decode_and_show_image(self, sample):
        sample = model.decode_first_stage(sample)
        return sample.cpu()

    def build_model(self):
        """The `build_model(...)` method returns a model and the returned model is set to `self._model` state."""

        import os

        import torch
        from diffusers import StableDiffusionPipeline

        print("loading model...")
        if torch.cuda.is_available():
            # TODO: Add config path after uploading to (and downloading from) the AWS server
            config_path = "config.yaml"
            config = OmegaConf.load(config_path)
            torch.set_grad_enabled(False)

            def load_model_from_config(config, ckpt, verbose=False):
                print(f"Loading model from {ckpt}")
                pl_sd = torch.load(ckpt, map_location="gpu")
                if "global_step" in pl_sd:
                    print(f"Global Step: {pl_sd['global_step']}")
                sd = pl_sd["state_dict"]
                model = instantiate_from_config(config.model)
                m, u = model.load_state_dict(sd, strict=False)
                if len(m) > 0 and verbose:
                    print("missing keys:")
                    print(m)
                if len(u) > 0 and verbose:
                    print("unexpected keys:")
                    print(u)

                return model

            # TODO: Add weights path here after uploading to (and downloading from) he AWS server
            weights_path = "/home/kush/diffusion/original-diffusers/models--CompVis--stable-diffusion-v-1-4-original/snapshots/ddc1b75c86ad6cba1ee990929497ad249112d069/sd-v1-4.ckpt"
            model = load_model_from_config(
                config, weights_path, verbose=True
            )

            # TODO: Add traced model path here after uploading to (and downloading from) the AWS server
            traced_model_path = "sd_amp_traced.pt"
            sd_fused = torch.jit.load(traced_model_path)
            sd_fused = sd_fused.to("cuda:0")

            model.apply_model = lambda x, t, c : sd_fused(_x = x, _t = t, _cnd = c)
            # warmup
            for i in range(3):
                model.apply_model(tmp_x, tmp_t, tmp_c)
            pipe = model
        else:
            pipe = None
            print("model set to None")
        return pipe

    def predict(self, dreams: List[Data], entry_time: int):
        if time.time() - entry_time > REQUEST_TIMEOUT:
            raise TimeoutException()

        height = width = IMAGE_SIZE
        num_inference_steps = 50 if dreams[0].high_quality else 25

        prompts = [dream.dream for dream in dreams]
        with autocast("cuda"):
            if torch.cuda.is_available():
                # preds = self._model(
                #     prompts,
                #     height=height,
                #     width=width,
                #     num_inference_steps=num_inference_steps,
                # )
                # pil_results = preds.images
                # for i, has_nsfw in enumerate(preds.nsfw_content_detected):
                #     if has_nsfw:
                #         pil_results[i] = Image.open("./assets/nsfw-warning.png")
                c = self._model.get_learned_conditioning(prompts)
                uc = self._model.get_learned_conditioning(len(c) * [""])
                sample_scaled, _ = self._model.sample_log(
                    cond=c,
                    batch_size=len(prompts),
                    ddim=True,
                    ddim_steps=num_inference_steps,
                    unconditional_guidance_scale=5.0,
                    unconditional_conditioning=uc)
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
                old_pool = app.POOL
                app.POOL = ThreadPoolExecutor(max_workers=1)
                old_pool.shutdown(wait=False)
                signal.signal(signal.SIGINT, lambda sig, frame: exit_threads(old_pool))
                self.num_failures += 1
                raise TimeoutException()

        uvicorn.run(app, host=self.host, port=self.port, timeout_keep_alive=30)
