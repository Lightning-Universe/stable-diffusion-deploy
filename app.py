import os
import time
import uuid
from typing import List

import lightning as L
import requests
from lightning.app.frontend import StaticWebFrontend

from dream import DreamSlackCommandBot, StableDiffusionServe
from dream.components.load_balancer import LoadBalancer


class ReactUI(L.LightningFlow):
    def configure_layout(self):
        return StaticWebFrontend(os.path.join(os.path.dirname(__file__), "dream", "ui", "build"))


class RootWorkFlow(L.LightningFlow):
    """
    autoscale_interval: time in seconds in which autoscale will run
    """

    def __init__(
        self,
        initial_num_workers=5,
        autoscale_interval=1 * 30,
        max_batch_size=12,
        batch_size_wait_s=5,
        gpu_type="gpu-fast",
        max_workers: int = 10,
        autoscale_down_threshold: int = None,
        autoscale_up_threshold: int = None,
    ):
        super().__init__()
        self._initial_num_workers = initial_num_workers
        self._num_workers = 0
        self._work_registry = {}
        self.autoscale_interval = autoscale_interval
        self.max_workers = max_workers
        self.autoscale_down_threshold = autoscale_down_threshold or initial_num_workers * max_batch_size
        self.autoscale_up_threshold = autoscale_up_threshold or initial_num_workers * max_batch_size
        self.fake_trigger = 0
        self.gpu_type = gpu_type
        self._last_autoscale = time.time()
        self.load_balancer = LoadBalancer(
            max_wait_time=batch_size_wait_s, max_batch_size=max_batch_size, cache_calls=True, parallel=True
        )
        for i in range(initial_num_workers):
            work = StableDiffusionServe(cloud_compute=L.CloudCompute(gpu_type), cache_calls=True, parallel=True)
            self.add_work(work)

        self.slack_bot = DreamSlackCommandBot(command="/inspire")
        self.printed_url = False
        self.slack_bot_url = ""
        self.dream_url = ""
        self.ui = ReactUI()

    @property
    def model_servers(self) -> List[StableDiffusionServe]:
        works = []
        for i in range(self._num_workers):
            work: StableDiffusionServe = self.get_work(i)
            works.append(work)
        return works

    def add_work(self, work):
        work_attribute = uuid.uuid4().hex
        work_attribute = f"model_serve_{self._num_workers}_{str(work_attribute)}"
        setattr(self, work_attribute, work)
        self._work_registry[self._num_workers] = work_attribute
        self._num_workers += 1

    def remove_work(self, index: int):
        work_attribute = self._work_registry[index]
        del self._work_registry[index]
        work = getattr(self, work_attribute)
        work.stop()
        self._num_workers -= 1

    def get_work(self, index: int):
        work_attribute = self._work_registry[index]
        work = getattr(self, work_attribute)
        return work

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
            self.fake_trigger += 1
            self.autoscale()
            self.load_balancer.update_servers(self.model_servers)

    def configure_layout(self):
        return [
            {
                "name": None,
                "content": self.ui,
            },
        ]

    def autoscale(self):
        """Upscale and down scale model inference works based on the number of requests."""
        if time.time() - self._last_autoscale < self.autoscale_interval:
            return

        num_requests = int(requests.get(f"{self.load_balancer.url}/num-requests").json())
        # num_requests = self.load_balancer.num_requests
        num_workers = len(self.model_servers)

        # upscale
        if num_requests > self.autoscale_up_threshold and num_workers < self.max_workers:
            idx = self._num_workers
            print(f"Upscale to {self._num_workers + 1}")
            work = StableDiffusionServe(
                cloud_compute=L.CloudCompute(self.gpu_type),
                cache_calls=True,
                parallel=True,
            )
            self.add_work(work)
            print(f"serve_work_{idx}")

        # downscale
        elif num_requests < self.autoscale_down_threshold and num_workers > self._initial_num_workers:
            idx = self._num_workers - 1
            print(f"Downscale to {idx}")
            print("prev num servers:", len(self.model_servers))
            self.remove_work(idx)
            print("new num servers:", len(self.model_servers))
            self.load_balancer.update_servers(self.model_servers)
        self._last_autoscale = time.time()


if __name__ == "__main__":
    app = L.LightningApp(RootWorkFlow())
