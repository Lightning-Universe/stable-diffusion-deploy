import os

from muse.components.stable_diffusion_serve import StableDiffusionServe


def test_custom_logic_check_bool():
    sd_variant = "https://huggingface.co/stabilityai/stable-diffusion-2-1/resolve/main/v2-1_768-ema-pruned.ckpt"
    sd_version = "2"
    custom_model_test = "True"

    envs = {
        "SD_VARIANT": sd_variant,
        "SD_VERSION": sd_version,
        "CUSTOM_MODEL_TEST": custom_model_test,
    }
    for env in envs:
        os.environ[env] = envs[env]

    model_info = StableDiffusionServe().is_custom_model()
    for env in envs:
        os.environ[env] = ""
    assert model_info["is_custom_model"] is True


def test_custom_logic_check_variant():
    sd_variant = "https://huggingface.co/stabilityai/stable-diffusion-2-1/resolve/main/v2-1_768-ema-pruned.ckpt"
    sd_version = "2"
    custom_model_test = "True"

    envs = {
        "SD_VARIANT": sd_variant,
        "SD_VERSION": sd_version,
        "CUSTOM_MODEL_TEST": custom_model_test,
    }
    for env in envs:
        os.environ[env] = envs[env]

    model_info = StableDiffusionServe().is_custom_model()
    for env in envs:
        os.environ[env] = ""
    assert model_info["sd_variant"] == sd_variant


def test_custom_logic_check_version():
    sd_variant = "https://huggingface.co/stabilityai/stable-diffusion-2-1/resolve/main/v2-1_768-ema-pruned.ckpt"
    sd_version = "2"
    custom_model_test = "True"

    envs = {
        "SD_VARIANT": sd_variant,
        "SD_VERSION": sd_version,
        "CUSTOM_MODEL_TEST": custom_model_test,
    }
    for env in envs:
        os.environ[env] = envs[env]

    model_info = StableDiffusionServe().is_custom_model()
    for env in envs:
        os.environ[env] = ""
    assert model_info["sd_version"] == sd_version
