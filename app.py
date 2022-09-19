import os
import time
from typing import List

import lightning as L
from lightning.app.frontend import StaticWebFrontend

from dream import DreamSlackCommandBot, StableDiffusionServe
from dream.components.load_balancer import LoadBalancer

AUTOSCALE_UP_THRESHOLD = 10
AUTOSCALE_DOWN_THRESHOLD = 1
MAX_WORKERS = 5


class ReactUI(L.LightningFlow):
    def configure_layout(self):
        return StaticWebFrontend(os.path.join(os.path.dirname(__file__), "dream", "ui", "build"))


class RootWorkFlow(L.LightningFlow):
    """
    health_check_interval: time in seconds in which health_check will run
    """

    def __init__(
        self,
        initial_num_workers=3,
        autoscale_interval=1 * 60,
        tolerable_failures=5,
        batch_size_wait_s=1,
        max_batch_size=4,
    ):
        super().__init__()
        self._last_autoscale = time.time()
        self.autoscale_interval = autoscale_interval  # in seconds
        self._initial_num_workers = self.num_workers = initial_num_workers
        self.tolerable_failures = tolerable_failures
        self.load_balancer = LoadBalancer(
            max_wait_time=batch_size_wait_s, max_batch_size=max_batch_size, cache_calls=True, parallel=True
        )
        for i in range(initial_num_workers):
            work = StableDiffusionServe(
                tolerable_failures=5, cloud_compute=L.CloudCompute("gpu"), cache_calls=True, parallel=True
            )
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
            self.autoscale()

    def configure_layout(self):
        return [
            {
                "name": None,
                "content": self.ui,
            },
        ]

    def autoscale(self):
        """Upscale and down scale model inference works based on the number of requests."""
        if time.time() - self._last_autoscale > self.autoscale_interval:
            return
        num_requests = self.load_balancer.num_requests
        num_workers = len(self.model_servers)

        # based on @lantiga's impl: https://github.com/Lightning-AI/LAI-Stable-Diffusion-App/tree/scale_model_trial1
        # upscale
        if num_requests > AUTOSCALE_UP_THRESHOLD and num_workers < MAX_WORKERS:
            work_index = len(self.model_servers)
            work = StableDiffusionServe(
                tolerable_failures=self.tolerable_failures,
                cloud_compute=L.CloudCompute("gpu"),
                cache_calls=True,
                parallel=True,
            )
            setattr(self, f"serve_work_{work_index}", work)
            self.num_workers += 1

        # downscale
        elif num_requests < AUTOSCALE_DOWN_THRESHOLD and not num_requests < self._initial_num_workers:
            for worker in self.model_servers[self._initial_num_workers :]:
                worker.stop()
                self.num_workers -= 1
        self._last_autoscale = time.time()


if __name__ == "__main__":
    app = L.LightningApp(RootWorkFlow())
