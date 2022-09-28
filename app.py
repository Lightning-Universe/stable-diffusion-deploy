import os
import time
import uuid
from typing import List

import lightning as L
import requests
from lightning.app.frontend import StaticWebFrontend

from muse import MuseSlackCommandBot, StableDiffusionServe
from muse.components.load_balancer import LoadBalancer


class ReactUI(L.LightningFlow):
    def configure_layout(self):
        return StaticWebFrontend(os.path.join(os.path.dirname(__file__), "muse", "ui", "build"))


class MuseFlow(L.LightningFlow):
    """The MuseFlow is a LightningFlow component that handles all the servers and uses load balancer to spawn up and
    shutdown based on current requests in the queue.

    Args:
        initial_num_workers: Number of works to start when app initializes.
        autoscale_interval: Number of seconds to wait before checking whether to upscale or downscale the works.
        max_batch_size: Number of requests to process at once.
        batch_timeout_secs: Number of seconds to wait before sending the requests to process.
        gpu_type: GPU type to use for the works.
        max_workers: Max numbers of works to spawn to handle the incoming requests.
        autoscale_down_limit: Lower limit to determine when to stop works.
        autoscale_up_limit: Upper limit to determine when to spawn up a new work.
    """

    def __init__(
        self,
        initial_num_workers=1,
        autoscale_interval=1 * 30,
        max_batch_size=8,
        batch_timeout_secs=10,
        gpu_type="gpu-fast",
        max_workers: int = 10,
        autoscale_down_limit: int = None,
        autoscale_up_limit: int = None,
    ):
        super().__init__()
        self.load_balancer_started = False
        self._initial_num_workers = initial_num_workers
        self._num_workers = 0
        self._work_registry = {}
        self.autoscale_interval = autoscale_interval
        self.max_workers = max_workers
        self.autoscale_down_limit = autoscale_down_limit or initial_num_workers
        self.autoscale_up_limit = autoscale_up_limit or initial_num_workers * max_batch_size
        self.fake_trigger = 0
        self.gpu_type = gpu_type
        self._last_autoscale = time.time()
        self.load_balancer = LoadBalancer(
            max_batch_size=max_batch_size, batch_timeout_secs=batch_timeout_secs, cache_calls=True, parallel=True
        )
        for i in range(initial_num_workers):
            work = StableDiffusionServe(cloud_compute=L.CloudCompute(gpu_type), cache_calls=True, parallel=True)
            self.add_work(work)

        self.slack_bot = MuseSlackCommandBot(command="/muse")
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

    def add_work(self, work) -> str:
        work_attribute = uuid.uuid4().hex
        work_attribute = f"model_serve_{self._num_workers}_{str(work_attribute)}"
        setattr(self, work_attribute, work)
        self._work_registry[self._num_workers] = work_attribute
        self._num_workers += 1
        return work_attribute

    def remove_work(self, index: int) -> str:
        work_attribute = self._work_registry[index]
        del self._work_registry[index]
        work = getattr(self, work_attribute)
        work.stop()
        self._num_workers -= 1
        return work_attribute

    def get_work(self, index: int):
        work_attribute = self._work_registry[index]
        work = getattr(self, work_attribute)
        return work

    def run(self):
        if os.environ.get("TESTING_LAI"):
            print("⚡ Lightning Dream App! ⚡")

        # provision load balancer and slack bot
        if not self.load_balancer.is_running:
            self.load_balancer.run([], start_run=False)
        if self.slack_bot is not None and not self.slack_bot.is_running:
            self.slack_bot.run("", start_run=False)

        for model_serve in self.model_servers:
            model_serve.run()

        if all(model_serve.url for model_serve in self.model_servers) and not self.load_balancer_started:
            # run the load balancer when all the model server is ready
            self.load_balancer.run([serve.url for serve in self.model_servers if serve.is_model_ready])
            self.load_balancer_started = True

        if self.load_balancer.url:  # hack for getting the work url
            self.dream_url = self.load_balancer.url
            if self.slack_bot is not None:
                self.slack_bot.run(self.load_balancer.url)
                self.slack_bot_url = self.slack_bot.url
                if self.slack_bot.url and not self.printed_url and self.load_balancer.servers:
                    print("Slack Bot Work ready with URL=", self.slack_bot.url)
                    print("model serve url=", self.load_balancer.url)
                    self.printed_url = True

        if self.load_balancer.url:
            self.load_balancer.update_servers(self.model_servers)
            self.fake_trigger += 1
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
        if time.time() - self._last_autoscale < self.autoscale_interval:
            return

        self.load_balancer.update_servers(self.model_servers)

        num_requests = int(requests.get(f"{self.load_balancer.url}/num-requests").json())
        num_workers = len(self.model_servers)

        # upscale
        if num_requests > self.autoscale_up_limit and num_workers < self.max_workers:
            idx = self._num_workers
            print(f"Upscale to {self._num_workers + 1}")
            work = StableDiffusionServe(
                cloud_compute=L.CloudCompute(self.gpu_type),
                cache_calls=True,
                parallel=True,
            )
            work.run()
            new_work_id = self.add_work(work)
            print("new work id:", new_work_id)

        # downscale
        elif num_requests < self.autoscale_down_limit and num_workers > self._initial_num_workers:
            idx = self._num_workers - 1
            print(f"Downscale to {idx}")
            print("prev num servers:", len(self.model_servers))
            removed_id = self.remove_work(idx)
            print("removed:", removed_id)
            print("new num servers:", len(self.model_servers))
            self.load_balancer.update_servers(self.model_servers)
        self._last_autoscale = time.time()


if __name__ == "__main__":
    app = L.LightningApp(MuseFlow())
