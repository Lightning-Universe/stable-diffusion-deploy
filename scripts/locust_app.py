import subprocess

import lightning as L
from lightning import LightningWork


class Locust(LightningWork):
    def __init__(self, num_users: int):
        super().__init__(port=8089, parallel=True, cloud_build_config=L.BuildConfig(requirements=["locust"]))
        self.num_users = num_users

    def run(self):
        cmd = " ".join(
            [
                "locust",
                "--master-host",
                str(self.host),
                "--master-port",
                str(self.port),
                "-u",
                str(self.num_users),
            ]
        )
        subprocess.Popen(cmd, shell=True).wait()


class RootFlow(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self.locust = Locust(1)

    def run(self, *args, **kwargs) -> None:
        self.locust.run()

    def configure_layout(self):
        return {"name": "Load test", "content": self.locust.url}


app = L.LightningApp(RootFlow())
