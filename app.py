import os
import time

import lightning as L
import requests
from lightning.app.frontend import StaticWebFrontend

from dream import DreamSlackCommandBot, StableDiffusionServe
from dream.components.load_balancer import LoadBalancer
from dream.components.work_manager import WorkManager


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
        batch_size_wait_s=10,
        gpu_type="gpu-fast",
        max_workers: int = 10,
        autoscale_down_threshold: int = 5,
        autoscale_up_threshold: int = 10,
    ):
        super().__init__()
        self._initial_num_workers = initial_num_workers
        self.autoscale_interval = autoscale_interval
        self.max_workers = max_workers
        self.autoscale_down_threshold = autoscale_down_threshold
        self.autoscale_up_threshold = autoscale_up_threshold
        self.fake_trigger = 0
        self.gpu_type = gpu_type
        self._last_autoscale = time.time()
        self.work_manager = WorkManager(groups=["serve_work"])
        self.load_balancer = LoadBalancer(
            max_wait_time=batch_size_wait_s, max_batch_size=max_batch_size, cache_calls=True, parallel=True
        )
        for i in range(initial_num_workers):
            work = StableDiffusionServe(cloud_compute=L.CloudCompute(gpu_type), cache_calls=True, parallel=True)
            self.work_manager.register_work(i, work)

        self.slack_bot = DreamSlackCommandBot(command="/dream")
        self.printed_url = False
        self.slack_bot_url = ""
        self.dream_url = ""
        self.ui = ReactUI()

    def run(self):
        if os.environ.get("TESTING_LAI"):
            print("⚡ Lightning Dream App! ⚡")

        model_servers = self.work_manager.get_works()
        for model_serve in model_servers:
            model_serve.run()
        if all(model_serve.url for model_serve in model_servers):
            # run the load balancer when all the model server is ready
            self.load_balancer.run([serve.url for serve in model_servers])

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

        model_servers = self.work_manager.get_works()
        num_requests = int(requests.get(f"{self.load_balancer.url}/num-requests").json())
        # num_requests = self.load_balancer.num_requests
        num_workers = len(self.model_servers)

        print(f"number of requests: {num_requests}")

        # based on @lantiga's impl: https://github.com/Lightning-AI/LAI-Stable-Diffusion-App/tree/scale_model_trial1
        # upscale
        if num_requests > self.autoscale_up_threshold and num_workers < self.max_workers:
            num_works = len(self.model_servers)
            print(f"Upscale to {num_works + 1}")
            work = StableDiffusionServe(
                cloud_compute=L.CloudCompute(self.gpu_type),
                cache_calls=True,
                parallel=True,
            )
            self.work_manager.register_work(num_works, work)
            model_servers = self.work_manager.get_works()
            self.load_balancer.update_servers(model_servers)

        # downscale
        elif num_requests < self.autoscale_down_threshold and num_workers > self._initial_num_workers:
            num_works = len(self.work_manager.num_workers)
            print(f"Downscale to {num_works - 1}")
            worker = self.work_manager.get_work(num_works - 1)
            worker.stop()
            self.work_manager.remove_work(num_works - 1)
            model_servers = self.work_manager.get_works()
            self.load_balancer.update_servers(model_servers)
        self._last_autoscale = time.time()


if __name__ == "__main__":
    app = L.LightningApp(RootWorkFlow())
