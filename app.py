import os
import time
from typing import List

import lightning as L
from lightning.app.frontend import StaticWebFrontend

from dream import DreamSlackCommandBot, StableDiffusionServe
from dream.components.load_balancer import LoadBalancer


class ReactUI(L.LightningFlow):
    def configure_layout(self):
        return StaticWebFrontend(os.path.join(os.path.dirname(__file__), "dream", "ui", "build"))


class RootWorkFlow(L.LightningFlow):
    last_health_check = time.time()
    health_check_frequency = 10  # in seconds

    def __init__(self, num_workers=3):
        super().__init__()
        self.num_workers = num_workers
        self.load_balancer = LoadBalancer(cache_calls=True, parallel=True)
        for i in range(num_workers):
            work = StableDiffusionServe(cloud_compute=L.CloudCompute("gpu"), cache_calls=True, parallel=True)
            setattr(self, f"serve_work_{i}", work)

        self.slack_bot = DreamSlackCommandBot(command="/dream")
        self.printed_url = False
        self.slack_bot_url = ""
        self.dream_url = ""
        self.ui = ReactUI()

    @property
    def model_servers(self) -> List[StableDiffusionServe]:
        works = []
        for i in range(self.num_workers):
            work: StableDiffusionServe = getattr(self, f"serve_work_{i}")
            works.append(work)
        return works

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
                self.slack_bot_url = self.slack_bot.url
                if self.slack_bot.url and not self.printed_url:
                    print("Slack Bot Work ready with URL=", self.slack_bot.url)
                    print("model serve url=", self.load_balancer.url)
                    self.printed_url = True

        if self.load_balancer.url:
            self.health_check(self.model_servers, frequency=self.health_check_frequency)

    def configure_layout(self):
        return [
            {
                "name": None,
                "content": self.ui,
            },
        ]

    def health_check(self, workers: List[StableDiffusionServe], frequency: int):
        """Restart the unhealthy workers.

        frequency: time in seconds in which health_check will run
        """
        if time.time() - self.last_health_check < frequency:
            return
        healthy_endpoints = []
        for worker in workers:
            if worker.has_succeeded:
                if worker.health_status is False:
                    worker.stop()
                    worker.run()
            else:
                healthy_endpoints.append(worker.url)
        self.load_balancer.update_servers(healthy_endpoints)


if __name__ == "__main__":
    app = L.LightningApp(RootWorkFlow())
