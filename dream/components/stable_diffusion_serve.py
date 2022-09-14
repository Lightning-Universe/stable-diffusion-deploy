import base64
import os.path
import tarfile
import time
import urllib.request
import uuid
from io import BytesIO
from typing import List

import lightning as L
import numpy as np
import torch
from fastapi import HTTPException
from lightning.app.api import Post
from lightning.app.structures import List as LightningList
from PIL import Image
from pydantic import BaseModel
from torch import autocast

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

    @staticmethod
    def download_weights(url: str, target_folder: str):
        dest = target_folder + f"/{os.path.basename(url)}"
        urllib.request.urlretrieve(url, dest)
        file = tarfile.open(dest)

        # extracting file
        file.extractall(target_folder)

    def build_model(self):
        """The `build_model(...)` method returns a model and the returned model is set to `self._model` state."""

        import os

        import torch
        from diffusers import StableDiffusionPipeline

        print("loading model...")
        if torch.cuda.is_available():
            weights_folder = "resources/stable-diffusion-v1-4"
            os.makedirs(weights_folder, exist_ok=True)

            print("Downloading weights...")
            self.download_weights(
                "https://lightning-dream-app-assets.s3.amazonaws.com/diffusers.tar.gz", weights_folder
            )

            repo_folder = f"{weights_folder}/Users/pritam/.cache/huggingface/diffusers/models--CompVis--stable-diffusion-v1-4/snapshots/a304b1ab1b59dd6c3ba9c40705c29c6de4144096"
            pipe = StableDiffusionPipeline.from_pretrained(
                repo_folder,
                revision="fp16",
                torch_dtype=torch.float16,
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
    num_images: int = 1
    image_size: int = 512


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
        # if not all(worker.is_running for worker in self.workers[:self.initial_num_workers]):
        #    self._last_autoscaled = time.time()
        #    return

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
