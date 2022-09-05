import base64
import queue
import time
import uuid
from dataclasses import dataclass
from io import BytesIO
from threading import Lock, Thread

import lightning as L
import numpy as np
import torch
from PIL import Image
from torch import autocast

# GPU Usage with different settings (image size , num images):
# 512, 1 => 7639MiB
# 512,2 => 10779MiB
# 512, 4 => 17039MiB
# 512, 9 => 23786MiB


REQUEST_TIMEOUT = 5 * 60


@dataclass
class FastAPIBuildConfig(L.BuildConfig):

    requirements = ["fastapi==0.78.0", "uvicorn==0.17.6"]


class StableDiffusionServe(L.LightningWork):
    def __init__(self, **kwargs):
        super().__init__(cloud_build_config=FastAPIBuildConfig(), **kwargs)

        self._model = None
        self._queue = queue.Queue(maxsize=0)
        self._results = {}

    def build_model(self):
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

    def run(self):
        import uvicorn
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel

        results_lock = Lock()

        if self._model is None:
            self._model = self.build_model()

        app = FastAPI()

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        class Data(BaseModel):
            dream: str
            num_images: int
            image_size: int

        @app.post("/api/predict/")
        def predict(data: Data):
            """Dream a dream."""
            job_uuid = uuid.uuid4()
            self._queue.put((job_uuid, data.dream, data.num_images, data.image_size))
            start = time.time()
            while True:
                if job_uuid in self._results:
                    with results_lock:
                        res = self._results.pop(job_uuid)
                    return res
                if time.time() - start > REQUEST_TIMEOUT:
                    break

            raise HTTPException(status_code=500, detail="Request timed out.")

        def worker():
            job_uuid, *args = self._queue.get()
            res = self.predict(*args)
            with results_lock:
                self._results[job_uuid] = res

        worker_thread = Thread(target=worker)
        worker_thread.start()

        uvicorn.run(app, host=self.host, port=self.port)
