import argparse

import numpy as np
import torch
from ldm.models.diffusion.ddim import DDIMSampler
from ldm.util import instantiate_from_config
from omegaconf import OmegaConf
from PIL import Image
from torch import autocast
from transformers import AutoFeatureExtractor

from muse.CONST import IMAGE_SIZE

# load safety model
safety_model_id = "CompVis/stable-diffusion-safety-checker"
safety_feature_extractor = AutoFeatureExtractor.from_pretrained(safety_model_id)


def load_model_from_config(config, ckpt, verbose=False):
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


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        type=str,
        default="configs/stable-diffusion/v1-inference.yaml",
        help="path to config which constructs model",
    )
    parser.add_argument(
        "--ckpt",
        type=str,
        default="models/ldm/stable-diffusion-v1/model.ckpt",
        help="path to checkpoint of model",
    )
    opt = parser.parse_args()

    config = OmegaConf.load(f"{opt.config}")
    model = load_model_from_config(config, f"{opt.ckpt}")

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    model = model.to(device)
    sampler = DDIMSampler(model)

    batch_size = len(opt.prompt)

    with torch.inference_mode(), autocast("cuda"), model.ema_scope():
        uc = model.get_learned_conditioning(batch_size * [""])
        c = model.get_learned_conditioning(prompts)
        shape = [4, IMAGE_SIZE // 8, IMAGE_SIZE // 8]
        samples_ddim, _ = sampler.sample(
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

        x_samples_ddim = model.decode_first_stage(samples_ddim)
        x_samples_ddim = torch.clamp((x_samples_ddim + 1.0) / 2.0, min=0.0, max=1.0)
        x_samples_ddim = x_samples_ddim.cpu().permute(0, 2, 3, 1).numpy()

        # SAFTY CHECKER GOES HERE
        x_checked_image = x_samples_ddim

        x_checked_image = (255.0 * x_checked_image).astype(np.uint8)
        pil_results = [Image.fromarray(x_sample) for x_sample in x_checked_image]
