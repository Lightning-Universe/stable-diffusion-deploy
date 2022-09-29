import subprocess

import lightning as L


class Locust(L.LightningWork):
    def __init__(self, locustfile: str, num_users: int = 10, port: int = 8089):
        super().__init__(port=port, parallel=True, cloud_build_config=L.BuildConfig(requirements=["locust"]))
        self.locustfile = locustfile
        self.num_users = num_users
        self.html_file = "locust_report.html"

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
                "-f",
                str(self.locustfile),
                "--html",
                str(self.html_file),
            ]
        )
        subprocess.Popen(cmd, shell=True).wait()
