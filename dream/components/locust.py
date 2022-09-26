import subprocess

from lightning import LightningWork


class Locust(LightningWork):
    def __init__(self, num_users: int):
        super().__init__(port=8089, parallel=True)
        self.num_users = num_users

    def run(self, host: str):
        cmd = " ".join(
            [
                "locust",
                "--master-host",
                str(self.host),
                "--master-port",
                str(self.port),
                "--host",
                str(host),
                "-u",
                str(self.num_users),
            ]
        )
        subprocess.Popen(cmd, shell=True).wait()
