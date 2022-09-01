from functools import partial

import gradio as gr
import numpy as np
import torch
from lightning.app.components.serve import ServeGradio
from PIL import Image
from torch import autocast

# GPU Usage with different settings (image size , num images):
# 512, 1 => 7639MiB
# 512,2 => 10779MiB
# 512, 4 => 17039MiB
# 512, 9 => 23786MiB

image_size_choices = [256, 512]


class StableDiffusionUI(ServeGradio):
    inputs = [
        gr.inputs.Textbox(default="cat reading a book", label="Enter the text prompt"),
        gr.Radio(value=1, choices=list(range(1, 10)), label="Number of images"),
        gr.Radio(value=512, choices=image_size_choices, label="Image Size"),
    ]
    outputs = gr.Gallery(type="pil")
    examples = [["a photograph of an astronaut riding a horse"], ["cat reading a book"]]
    enable_queue = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        else:
            pipe = None
        print("model loaded")
        return pipe

    def predict(self, prompt, num_images, image_size):
        height, width = image_size, image_size
        prompts = [prompt] * int(num_images)
        results = []
        with autocast("cuda"):
            # predicting in chunks to save cuda out of memory error
            chunk_size = 3
            for i in range(0, num_images, chunk_size):
                if torch.cuda.is_available():
                    results.extend(self.model(prompts[i : i + chunk_size], height=height, width=width)["sample"])
                else:
                    results.extend([Image.fromarray(np.random.randint(0, 255, (height, width, 3), dtype="uint8"))])
            return results

    def run(self, *args, **kwargs):
        if self._model is None:
            self._model = self.build_model()
        fn = partial(self.predict, *args, **kwargs)
        fn.__name__ = self.predict.__name__
        gr.Interface(
            fn=fn,
            inputs=self.inputs,
            outputs=self.outputs,
            examples=self.examples,
            title="Visualize your words",
        ).launch(
            server_name=self.host,
            server_port=self.port,
            enable_queue=self.enable_queue,
        )
