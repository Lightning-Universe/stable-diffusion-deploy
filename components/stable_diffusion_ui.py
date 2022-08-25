from functools import partial

import gradio as gr
import lightning as L
from lightning.app.components.serve import ServeGradio
from torch import autocast

# GPU Usage with different settings (image size , num images):
# 512, 1 => 7639MiB
# 512,2 => 10779MiB
# 512, 4 => 17039MiB
# 512, 9 => 23786MiB

image_size_choices = [256, 512]

description = """Picture says a thousand words! Generate image from text prompts with the latest AI technology "Stable Diffusion".

<center><img src="https://i.ibb.co/dKmydFG/Generate-Image-from-Text.jpg" alt="generate image from text"></center>

Enter a text in the app below and click on the submit button to generate images.
"""

article = """
<br>

Stable Diffusion is an AI model that will empower billions of people to create stunning art within seconds.
It is a breakthrough in speed and quality meaning that it can run on consumer GPUs.

Read the <a href="https://stability.ai/blog/stable-diffusion-public-release">Stable Diffusion Public Release</a> blog post from Stability AI
"""


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
        pipe = StableDiffusionPipeline.from_pretrained(
            "CompVis/stable-diffusion-v1-4",
            revision="fp16",
            torch_dtype=torch.float16,
            use_auth_token=access_token,
        )
        pipe = pipe.to("cuda")
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
                results.extend(
                    self.model(prompts[i : i + chunk_size], height=height, width=width)[
                        "sample"
                    ]
                )
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
            description=description,
            article=article,
        ).launch(
            server_name=self.host,
            server_port=self.port,
            enable_queue=self.enable_queue,
        )
