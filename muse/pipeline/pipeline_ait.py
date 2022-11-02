import torch
from aitemplate.stable_diffusion import StableDiffusionAITPipeline


class StableDiffusionAIT:
    def __init__(self, token):
        self.model = StableDiffusionAITPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            revision="fp16",
            torch_dtype=torch.float16,
            use_auth_token=token,
        ).to("cuda")
        torch.cuda.empty_cache()

    def __call__(self, prompts, height, width, num_inference_steps):

        images = self.model(prompts, height, width, num_inference_steps).images
        return images
