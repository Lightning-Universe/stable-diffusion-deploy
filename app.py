import lightning as L

from components.slack_command import SlackCommandWork
from components.stable_diffusion_ui import StableDiffusionUI


class RootWorkFlow(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self.model_demo = StableDiffusionUI(
            cloud_compute=L.CloudCompute("gpu"), parallel=True
        )
        self.slack_work = SlackCommandWork(parallel=True)

    def run(self):
        self.model_demo.run()
        if self.model_demo.is_running:
            self.slack_work.run(self.model_demo.url)

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
