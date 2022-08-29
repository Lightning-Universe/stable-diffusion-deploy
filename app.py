import os

import lightning as L

from dream import DreamSlackCommandBot, StableDiffusionUI


class RootWorkFlow(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self.model_demo = StableDiffusionUI(cloud_compute=L.CloudCompute("gpu"), parallel=True)
        self.slack_bot = DreamSlackCommandBot(parallel=True)
        self.printed_url = False

    def run(self):
        if os.environ.get("TESTING_LAI"):
            print("⚡ Lightning Dream App! ⚡")
        self.model_demo.run()
        if self.model_demo.url:  # hack for getting the work url
            self.slack_bot.run(self.model_demo.url)
            if self.slack_bot.url and not self.printed_url:
                print("Slack work ready with url=", self.slack_bot.url)
                self.printed_url = True

    def configure_layout(self):
        return [
            {"name": "Visualize your words", "content": self.model_demo},
            {
                "name": "Blog",
                "content": "https://wandb.ai/telidavies/ml-news/reports/Stable-Diffusion-A-Model-To-Rival-DALL-E-2-With-Fewer-Restrictions--VmlldzoyNDY3NTU5",
            },
        ]


if __name__ == "__main__":
    app = L.LightningApp(RootWorkFlow())
