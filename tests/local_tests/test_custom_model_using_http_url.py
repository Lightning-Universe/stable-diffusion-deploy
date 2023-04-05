import io
import os
from contextlib import redirect_stdout

from lightning.app.testing.testing import LightningTestApp, application_testing


class LightningAppCustomModelTest(LightningTestApp):
    def run_once(self) -> bool:
        f = io.StringIO()
        with redirect_stdout(f):
            super().run_once()
        out = f.getvalue()
        assert "is loaded.\n" == out[-11:]
        return True


def test_custom_model_via_url_is_available():
    cwd = os.getcwd()
    cwd = os.path.join(cwd, "app.py")
    envs = {
        "SD_VARIANT": "https://huggingface.co/stabilityai/stable-diffusion-2-1/resolve/main/v2-1_768-ema-pruned.ckpt",
        "SD_VERSION": "2",
        "CUSTOM_MODEL_TEST": "True",
    }
    for env in envs:
        os.environ[env] = envs[env]

    command_line = [
        cwd,
        "--blocking",
        "False",
        "--open-ui",
        "False",
    ]
    result = application_testing(LightningAppCustomModelTest, command_line)
    for env in envs:
        os.environ[env] = ""
    assert result.exit_code == 0
