import lightning as L

from components.slack_command_bot import SlackCommandBot
from components.stable_diffusion_ui import StableDiffusionUI


class RootWorkFlow(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self.model_demo = StableDiffusionUI(
            cloud_compute=L.CloudCompute("gpu"), parallel=True
        )
        self.slack_work = SlackCommandBot(parallel=True)
        self.printed_url = False

    def run(self):
        self.model_demo.run()
        if self.model_demo.url:
            self.slack_work.run(self.model_demo.url)
            if self.slack_work.url and not self.printed_url:
                print(self.slack_work.url)
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
