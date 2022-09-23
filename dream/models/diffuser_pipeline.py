from typing import List, Optional, Union

import torch
from diffusers import PNDMScheduler
from PIL import Image
from tqdm import tqdm
from transformers import CLIPTokenizer


class StableDiffusionPipelineTraced:
    def __init__(self, pretrained_path):
        super().__init__()
        self.tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-large-patch14")
        self.scheduler = PNDMScheduler.from_config(pretrained_path / "scheduler_config.json")
        self.scheduler = self.scheduler.set_format("pt")
        self.text_encoder = torch.jit.load(pretrained_path / "text_encoder_traced.pt")
        self.unet = torch.jit.load(pretrained_path / "unet_traced.pt")
        self.vae_post_quant_conv = torch.jit.load(pretrained_path / "vae_post_quant_conv_traced.pt")
        self.vae_decoder = torch.jit.load(pretrained_path / "vae_decoder.pt")
        self.device = "cuda"

        with torch.autocast("cuda"):
            # warmup
            self("warmup traced modules please", num_inference_steps=7)

    @torch.inference_mode()
    def __call__(
        self,
        prompt: Union[str, List[str]],
        height: Optional[int] = 512,
        width: Optional[int] = 512,
        num_inference_steps: Optional[int] = 50,
        guidance_scale: Optional[float] = 7.5,
        generator: Optional[torch.Generator] = None,
    ):
        if isinstance(prompt, str):
            batch_size = 1
        elif isinstance(prompt, list):
            batch_size = len(prompt)

        # get prompt text embeddings
        text_input = self.tokenizer(
            prompt,
            padding="max_length",
            max_length=self.tokenizer.model_max_length,
            truncation=True,
            return_tensors="pt",
        )
        max_length = text_input.input_ids.shape[-1]
        uncond_input = self.tokenizer(
            [""] * batch_size, padding="max_length", max_length=max_length, return_tensors="pt"
        )

        text_embeddings = self.text_encoder(text_input.input_ids.to(self.device))[0]
        uncond_embeddings = self.text_encoder(uncond_input.input_ids.to(self.device))[0]

        # For classifier free guidance, we need to do two forward passes.
        # Here we concatenate the unconditional and text embeddings into a single batch
        # to avoid doing two forward passes
        text_embeddings = torch.cat([uncond_embeddings, text_embeddings])

        # get the initial random noise unless the user supplied it

        # Unlike in other pipelines, latents need to be generated in the target device
        # for 1-to-1 results reproducibility with the CompVis implementation.
        # However this currently doesn't work in `mps`.
        latents_shape = (batch_size, 4, height // 8, width // 8)
        latents = torch.randn(
            latents_shape,
            generator=generator,
            device=self.device,
        )

        # set timesteps
        self.scheduler.set_timesteps(num_inference_steps, offset=1)

        for i, t in enumerate(tqdm(self.scheduler.timesteps)):
            # expand the latents if we are doing classifier free guidance
            latent_model_input = torch.cat([latents] * 2)
            timesteps = t.to(torch.float32)[None].to(self.device)
            # predict the noise residual

            noise_pred = self.unet(latent_model_input, timesteps, text_embeddings)[0]

            # perform guidance
            noise_pred_uncond, noise_pred_text = noise_pred.chunk(2)
            noise_pred = noise_pred_uncond + guidance_scale * (noise_pred_text - noise_pred_uncond)

            # compute the previous noisy sample x_t -> x_t-1
            latents = self.scheduler.step(noise_pred, t, latents).prev_sample

        # scale and decode the image latents with vae
        latents = 1 / 0.18215 * latents

        z = self.vae_post_quant_conv(latents)
        image = self.vae_decoder(z)

        image = (image / 2 + 0.5).clamp(0, 1)
        image = image.cpu().permute(0, 2, 3, 1).numpy()

        return self.numpy_to_pil(image)

    def numpy_to_pil(self, images):
        images = (images * 255).round().astype("uint8")
        pil_images = [Image.fromarray(image) for image in images]
        return pil_images
