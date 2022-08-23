import gradio as gr
import os
import lightning as L
from lightning.app.components.serve import ServeGradio


class StableDiffusionUI(ServeGradio):
    inputs = gr.inputs.Textbox(default='cat reading a book', label='Enter the text prompt')
    outputs = gr.outputs.Image(type="pil")
    examples = [["golden puppy playing in a pool"], ["cat reading a book"]]

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

    def predict(self, prompt):
        from torch import autocast
        with autocast("cuda"):
            image = self.model(prompt)["sample"][0]
        return image


class RootFlow(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self.model_demo = StableDiffusionUI(cloud_compute=L.CloudCompute("gpu"))
    
    def run(self):
        self.model_demo.run()
    
    def configure_layout(self):
        return [{"name": "Model Demo", "content": self.model_demo}]


if __name__=="__main__":
    app = L.LightningApp(RootFlow())
