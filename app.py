import os

import lightning as L
from lightning.app.frontend import StaticWebFrontend
from lightning.app.structures import List as LightningList

from dream import DreamSlackCommandBot, StableDiffusionServe
from dream.components.load_balancer import LoadBalancer


class ReactUI(L.LightningFlow):
    def configure_layout(self):
        return StaticWebFrontend(os.path.join(os.path.dirname(__file__), "dream", "ui", "build"))


class RootWorkFlow(L.LightningFlow):
    def __init__(self, num_workers=2):
        super().__init__()
        self.num_workers = num_workers
        self.load_balancer = LoadBalancer(cache_calls=True, parallel=True)
        self.model_servers = LightningList(
            *[
                StableDiffusionServe(cloud_compute=L.CloudCompute("gpu"), cache_calls=True, parallel=True)
                for _ in range(num_workers)
            ]
        )

        if "SIGNING_SECRET" in os.environ:
            self.slack_bot = DreamSlackCommandBot(command="/dream")
        else:
            self.slack_bot = None
        self.printed_url = False
        self.dream_url = ""
        self.ui = ReactUI()

    def run(self):
        if os.environ.get("TESTING_LAI"):
            print("⚡ Lightning Dream App! ⚡")

        for model_serve in self.model_servers:
            model_serve.run()
        if all(model_serve.url for model_serve in self.model_servers):
            # run the load balancer when all the model server is ready
            self.load_balancer.run([serve.url for serve in self.model_servers])

        if self.load_balancer.url:  # hack for getting the work url
            self.dream_url = self.load_balancer.url

            if self.slack_bot is not None:
                self.slack_bot.run(self.load_balancer.url)
                if self.slack_bot.url and not self.printed_url:
                    print("Slack Bot Work ready with URL=", self.slack_bot.url)
                    print("model serve url=", self.load_balancer.url)
                    self.printed_url = True

    def configure_layout(self):
        return [
            {
                "name": None,
                "content": self.ui,
            },
        ]


if __name__ == "__main__":
    app = L.LightningApp(RootWorkFlow())
