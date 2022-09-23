from functools import partial
from typing import List, Optional, Union

import lightning as L
import torch
from diffusers import (
    AutoencoderKL,
    DiffusionPipeline,
    PNDMScheduler,
    UNet2DConditionModel,
)
from diffusers.pipelines.stable_diffusion.safety_checker import (
    StableDiffusionSafetyChecker,
)
from transformers import CLIPFeatureExtractor, CLIPTextModel, CLIPTokenizer


def unet_forward(
    self,
    sample: torch.FloatTensor,
    timestep: Union[torch.Tensor, float, int],
    encoder_hidden_states: torch.Tensor,
    return_dict: bool = True,
):
    if self.config.center_input_sample:
        sample = 2 * sample - 1.0

    timesteps = timestep

    # broadcast to batch dimension in a way that's compatible with ONNX/Core ML

    t_emb = self.time_proj(timesteps)
    emb = self.time_embedding(t_emb)

    # 2. pre-process
    sample = self.conv_in(sample)

    # 3. down
    down_block_res_samples = (sample,)
    for downsample_block in self.down_blocks:
        if hasattr(downsample_block, "attentions") and downsample_block.attentions is not None:
            sample, res_samples = downsample_block(
                hidden_states=sample, temb=emb, encoder_hidden_states=encoder_hidden_states
            )
        else:
            sample, res_samples = downsample_block(hidden_states=sample, temb=emb)

        down_block_res_samples += res_samples

    # 4. mid
    sample = self.mid_block(sample, emb, encoder_hidden_states=encoder_hidden_states)

    # 5. up
    for upsample_block in self.up_blocks:
        res_samples = down_block_res_samples[-len(upsample_block.resnets) :]
        down_block_res_samples = down_block_res_samples[: -len(upsample_block.resnets)]

        if hasattr(upsample_block, "attentions") and upsample_block.attentions is not None:
            sample = upsample_block(
                hidden_states=sample,
                temb=emb,
                res_hidden_states_tuple=res_samples,
                encoder_hidden_states=encoder_hidden_states,
            )
        else:
            sample = upsample_block(hidden_states=sample, temb=emb, res_hidden_states_tuple=res_samples)

    # 6. post-process
    # make sure hidden states is in float32
    # when running in half-precision
    sample = self.conv_norm_out(sample.float()).type(sample.dtype)
    sample = self.conv_act(sample)
    sample = self.conv_out(sample)

    return sample


class StableDiffusionPipeline(DiffusionPipeline):
    def __init__(
        self,
        vae: AutoencoderKL,
        text_encoder: CLIPTextModel,
        tokenizer: CLIPTokenizer,
        unet: UNet2DConditionModel,
        scheduler: PNDMScheduler,
        safety_checker: StableDiffusionSafetyChecker,
        feature_extractor: CLIPFeatureExtractor,
    ):
        super().__init__()
        scheduler = scheduler.set_format("pt")
        self.register_modules(
            vae=vae,
            text_encoder=text_encoder,
            tokenizer=tokenizer,
            unet=unet,
            scheduler=scheduler,
            safety_checker=safety_checker,
            feature_extractor=feature_extractor,
        )

    def enable_attention_slicing(self, slice_size: Optional[Union[str, int]] = "auto"):
        r"""Enable sliced attention computation.

        When this option is enabled, the attention module will split the input tensor in slices, to compute attention
        in several steps. This is useful to save some memory in exchange for a small speed decrease.

        Args:
            slice_size (`str` or `int`, *optional*, defaults to `"auto"`):
                When `"auto"`, halves the input to the attention heads, so attention will be computed in two steps. If
                a number is provided, uses as many slices as `attention_head_dim // slice_size`. In this case,
                `attention_head_dim` must be a multiple of `slice_size`.
        """
        if slice_size == "auto":
            # half the attention head size is usually a good trade-off between
            # speed and memory
            slice_size = self.unet.config.attention_head_dim // 2
        self.unet.set_attention_slice(slice_size)

    def disable_attention_slicing(self):
        r"""Disable sliced attention computation.

        If `enable_attention_slicing` was previously invoked, this method will go back to computing attention in one
        step.
        """
        # set slice_size = `None` to disable `attention slicing`
        self.enable_attention_slicing(None)

    @torch.inference_mode()
    def __call__(
        self,
        prompt: Union[str, List[str]],
        height: Optional[int] = 512,
        width: Optional[int] = 512,
        num_inference_steps: Optional[int] = 1,
        guidance_scale: Optional[float] = 7.5,
        eta: Optional[float] = 0.0,
        generator: Optional[torch.Generator] = None,
        latents: Optional[torch.FloatTensor] = None,
        output_type: Optional[str] = "pil",
        return_dict: bool = True,
        **kwargs,
    ):

        if isinstance(prompt, str):
            batch_size = 1
        elif isinstance(prompt, list):
            batch_size = len(prompt)
        else:
            raise ValueError(f"`prompt` has to be of type `str` or `list` but is {type(prompt)}")

        if height % 8 != 0 or width % 8 != 0:
            raise ValueError(f"`height` and `width` have to be divisible by 8 but are {height} and {width}.")

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

        scripted_module = torch.jit.trace(
            self.text_encoder, example_inputs=uncond_input.input_ids.to(self.device), strict=False
        )
        with open("traced_modules/text_encoder_traced.pt", "wb") as f:
            torch.jit.save(scripted_module, f)

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

        for i, t in enumerate(self.progress_bar(self.scheduler.timesteps)):
            # expand the latents if we are doing classifier free guidance
            latent_model_input = torch.cat([latents] * 2)
            timesteps = t.to(torch.float32)[None].to(self.device)
            # predict the noise residual
            self.unet.forward = partial(self.unet.forward, return_dict=False)

            scripted_module = torch.jit.trace(
                self.unet, example_inputs=(latent_model_input, timesteps, text_embeddings)
            )
            with open("traced_modules/unet_traced.pt", "wb") as f:
                torch.jit.save(scripted_module, f)

            noise_pred = self.unet(
                latent_model_input, timesteps, encoder_hidden_states=text_embeddings, return_dict=False
            )[0]

            # perform guidance
            noise_pred_uncond, noise_pred_text = noise_pred.chunk(2)
            noise_pred = noise_pred_uncond + guidance_scale * (noise_pred_text - noise_pred_uncond)

            # compute the previous noisy sample x_t -> x_t-1
            latents = self.scheduler.step(noise_pred, t, latents).prev_sample

        # scale and decode the image latents with vae
        latents = 1 / 0.18215 * latents

        scripted_module = torch.jit.trace(self.vae.post_quant_conv, example_inputs=latents)
        with open("traced_modules/vae_post_quant_conv_traced.pt", "wb") as f:
            torch.jit.save(scripted_module, f)

        z = self.vae.post_quant_conv(latents)
        scripted_module = torch.jit.trace(self.vae.decoder, example_inputs=z)
        with open("traced_modules/vae_decoder.pt", "wb") as f:
            torch.jit.save(scripted_module, f)

        image = self.vae.decode(latents, return_dict=False)[0]
        image = (image / 2 + 0.5).clamp(0, 1)
        image = image.cpu().permute(0, 2, 3, 1).numpy()

        return self.numpy_to_pil(image)


class Work(L.LightningWork):
    def __init__(self):
        super().__init__()
        # self.drive_1 = Drive("lit://drive_1", component_name='pipe_work')
        self._pipe = StableDiffusionPipeline.from_pretrained(
            "CompVis/stable-diffusion-v1-4",
            revision="fp16",
            torch_dtype=torch.float16,
            use_auth_token="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",
        )
        self._pipe.to("cuda")

    def run(self, prompts):
        with torch.autocast("cuda"):
            img = self._pipe(prompts)[0]

        # self.drive_1.put('traced_modules/text_encoder_traced.pt')
        # self.drive_1.put('traced_modules/unet_traced.pt')
        # self.drive_1.put('traced_modules/vae_post_quant_conv_traced.pt')
        # self.drive_1.put('traced_modules/vae_decoder.pt')
        print("done..........")


class Flow(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self._pipe_work = Work()

    def run(self):
        prompt = ["a photograph of an astronaut riding a horse"] * 2
        self._pipe_work.run(prompt)


app = L.LightningApp(Flow())
