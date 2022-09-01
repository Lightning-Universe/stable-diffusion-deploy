import os

import lightning as L
from lightning.app.frontend import StaticWebFrontend

from dream import DreamSlackCommandBot, StableDiffusionUI


class ReactUI(L.LightningFlow):
    def configure_layout(self):
        return StaticWebFrontend(os.path.join(os.path.dirname(__file__), "dream", "ui", "build"))


class RootWorkFlow(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self.model_demo = StableDiffusionUI(cloud_compute=L.CloudCompute("gpu"))

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
        self.model_demo.run()
        if self.model_demo.url:  # hack for getting the work url
            self.dream_url = self.model_demo.url

            if self.slack_bot is not None:
                self.slack_bot.run(self.model_demo.url)
                if self.slack_bot.url and not self.printed_url:
                    print("Slack work ready with url=", self.slack_bot.url)
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
