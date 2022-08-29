r"""
To test a lightning app:
1. Use LightningTestApp which is a subclass of LightningApp.
2. Subclass run_once in LightningTestApp.
3. in run_once, come up with a way to verify the behavior you wanted.

run_once runs your app through one cycle of the event loop and then terminates
"""
import io
import os
from contextlib import redirect_stdout

from lightning.app.testing.testing import LightningTestApp, application_testing

os.environ["TESTING_LAI"] = "true"


class LightningAppTestInt(LightningTestApp):
    def run_once(self) -> bool:
        f = io.StringIO()
        with redirect_stdout(f):
            super().run_once()
        out = f.getvalue()
        assert "⚡ Lightning Dream App! ⚡\n" == out
        return True


def test_research_app():
    cwd = os.getcwd()
    cwd = os.path.join(cwd, "app.py")
    command_line = [
        cwd,
        "--blocking",
        "False",
        "--open-ui",
        "False",
    ]
    result = application_testing(LightningAppTestInt, command_line)
    assert result.exit_code == 0
