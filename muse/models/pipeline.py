import numpy as np
import torch
from PIL import Image
from torch import autocast


def load_model_from_config(config, ckpt, verbose=False):
    from ldm.util import instantiate_from_config

    print(f"Loading model from {ckpt}")
    pl_sd = torch.load(ckpt, map_location="cpu")
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

    model.cuda()
    model.eval()
    return model


class StableDiffusionModel:
    def __init__(self, model_path):
        from ldm.models.diffusion.ddim import DDIMSampler
        from omegaconf import OmegaConf

        config_path = model_path / "v1-inference.yml"
        weights_path = model_path / "sd-v1-4.ckpt"
        config = OmegaConf.load(f"{config_path}")
        self.model = load_model_from_config(config, f"{weights_path}")
        self.sampler = DDIMSampler(self.model)
        self.device = torch.device("cuda")
        self.model = self.model.to(self.device)
        torch.cuda.empty_cache()

    def __call__(self, prompts, height, width, num_inference_steps):
        batch_size = len(prompts)

        with torch.inference_mode(), autocast("cuda"), self.model.ema_scope():
            torch.cuda.empty_cache()
            uc = self.model.get_learned_conditioning(batch_size * [""])
            c = self.model.get_learned_conditioning(prompts)
            shape = [4, height // 8, width // 8]
            samples_ddim, _ = self.sampler.sample(
                S=num_inference_steps,
                conditioning=c,
                batch_size=batch_size,
                shape=shape,
                verbose=False,
                unconditional_guidance_scale=7.5,
                unconditional_conditioning=uc,
                eta=0.0,
                x_T=None,
            )

            x_samples_ddim = self.model.decode_first_stage(samples_ddim)
            x_samples_ddim = torch.clamp((x_samples_ddim + 1.0) / 2.0, min=0.0, max=1.0)
            x_samples_ddim = x_samples_ddim.cpu().permute(0, 2, 3, 1).numpy()

            x_samples_ddim = (255.0 * x_samples_ddim).astype(np.uint8)
            pil_results = [Image.fromarray(x_sample) for x_sample in x_samples_ddim]

        return pil_results
