import base64
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from io import BytesIO
import time
from typing import List
import uuid

import lightning as L
import numpy as np
import torch
from fastapi import HTTPException
from lightning.app.structures import List as LightningList
from lightning.app.api import Post
from lightning_app.storage import Drive
from PIL import Image
from torch import autocast
from pydantic import BaseModel


REQUEST_TIMEOUT = 5 * 60
AUTOSCALE_UP_THRESHOLD = 10
AUTOSCALE_DOWN_THRESHOLD = 1
AUTOSCALE_EVAL_FREQUENCY = 1 * 60


class ModelInference(L.LightningWork):
    def __init__(self, compute_type="gpu", **kwargs):
        super().__init__(cloud_compute=L.CloudCompute(compute_type), cache_calls=False, parallel=True, **kwargs)
        self._model = None
        self.busy = False
        self.results = None

    def build_model(self):
        """The `build_model(...)` method returns a model and the returned model is set to `self._model` state."""
        import os

        import torch
        from diffusers import StableDiffusionPipeline

        access_token = os.environ.get("access_token")

        # make sure you're logged in with `huggingface-cli login`
        print("loading model...")
        if torch.cuda.is_available():
            pipe = StableDiffusionPipeline.from_pretrained(
                "CompVis/stable-diffusion-v1-4",
                revision="fp16",
                torch_dtype=torch.float16,
                use_auth_token=access_token,
            )
            pipe = pipe.to("cuda")
            print("model loaded")
        else:
            pipe = None
            print("model set to None")
        return pipe

    def predict(self, dream: str, num_images: int, image_size: int):
        if self._model is None:
            self._model = self.build_model()
        height, width = image_size, image_size
        prompts = [dream] * int(num_images)
        pil_results = []
        with autocast("cuda"):
            # predicting in chunks to save cuda out of memory error
            chunk_size = 3
            for i in range(0, num_images, chunk_size):
                if torch.cuda.is_available():
                    pil_results.extend(self._model(prompts[i : i + chunk_size], height=height, width=width)["sample"])
                else:
                    pil_results.extend([Image.fromarray(np.random.randint(0, 255, (height, width, 3), dtype="uint8"))])

        results = []
        for image in pil_results:
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            results.append(f"data:image/png;base64,{img_str}")
        return results

    def run(self, uuid: str, dream: str, num_images: int, image_size: int):
        if uuid == "":
            return

        self.busy = True
        if self._model is None:
            self._model = self.build_model()
        images = self.predict(uuid, dream, num_images, image_size)
        self.results = (uuid, images)
        self.busy = False


class Data(BaseModel):
    dream: str
    num_images: int
    image_size: int


class StableDiffusionServe(L.LightningFlow):
    """Serves the Stable Diffusion model."""

    def __init__(self, initial_num_workers=1, worker_compute_type="gpu", **kwargs):
        super().__init__(**kwargs)

        self.bootstrapped = False
        self.workers: List[ModelInference] = LightningList(*[ModelInference() for _ in range(initial_num_workers)])
        self.initial_num_workers = initial_num_workers
        self.worker_compute_type = worker_compute_type
        self.requests = []
        self.results = {}
        self.foo = 1
        self._last_autoscaled = time.time()

    def handle_predict(self, data: Data):
        job_uuid = uuid.uuid4().hex
        print(job_uuid, data)
        print("PRE", self.requests)
        self.requests.append([job_uuid, data.dream, data.num_images, data.image_size])
        print("POST", self.requests)

        # return "foo"

        # This one jams the whole thing
        start = time.time()
        while True:
            if job_uuid in self.results:
                results = self.results.pop(job_uuid)
                return results
            if time.time() - start > REQUEST_TIMEOUT:
                break
            time.sleep(0.1)

        raise HTTPException(status_code=500, detail="Request timed out.")

    def configure_api(self):
        return [Post(route="/api/predict", method=self.handle_predict)]

    def autoscale(self):
        num_requests = len(self.requests)

        if num_requests > AUTOSCALE_UP_THRESHOLD:
            self.workers.append(ModelInference())

        if num_requests < AUTOSCALE_DOWN_THRESHOLD and not num_requests < self.initial_num_workers:
            for worker in self.workers:
                if not worker.busy:
                    worker = self.workers.pop()
                    worker.stop()

    def run(self, *args, **kwargs) -> None:
        #if not all(worker.is_running for worker in self.workers[:self.initial_num_workers]):
        #    self._last_autoscaled = time.time()
        #    return
        self.foo += 1

        if not self.bootstrapped:
            for worker in self.workers:
                worker.run("", "", 0, 0)
            self.bootstrapped = True
            self._last_autoscaled = time.time()

        print("REQUESTS", self.requests)
        for worker in self.workers:
            if not worker.busy and worker.results is not None:
                job_uuid, *images = worker.results
                self.results[job_uuid] = images

        if self.requests:
            print("C1")
            job_uuid, *inputs = self.requests[0]

            for worker in self.workers:
                if not worker.busy:
                    self.requests.pop(0)
                    worker.run(job_uuid, *inputs)
                if not self.requests:
                    break

        if time.time() - self._last_autoscaled > AUTOSCALE_EVAL_FREQUENCY:
            self.autoscale()
            self._last_autoscaled = time.time()
