import os

import lightning as L
from lightning.app.frontend import StaticWebFrontend

from dream import DreamSlackCommandBot, StableDiffusionServe


class ReactUI(L.LightningFlow):
    def configure_layout(self):
        return StaticWebFrontend(os.path.join(os.path.dirname(__file__), "dream", "ui", "build"))


class RootWorkFlow(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self.model_serve = StableDiffusionServe(cloud_compute=L.CloudCompute("gpu"), cache_calls=True, parallel=True)

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
        self.model_serve.run()
        if self.model_serve.url:  # hack for getting the work url
            self.dream_url = self.model_serve.url

            if self.slack_bot is not None:
                self.slack_bot.run(self.model_serve.url)
                if self.slack_bot.url and not self.printed_url:
                    print("Slack Bot Work ready with URL=", self.slack_bot.url)
                    print("model serve url=", self.model_serve.url)
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
