import os

import lightning as L

from .slack_api import app as api


class SlackCommandWork(L.LightningWork):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self, inference_server_url: str, *args, **kwargs) -> None:
        print("starting Slack Listener")
        print(args)
        api.url = inference_server_url
        api.run(host=self.host, port=8001)


# class SlackRootFlow(L.LightningFlow):
#     def __init__(self):
#         super().__init__()
#         self.slack_work = SlackCommandWork()

#     def run(self):
#         self.slack_work.run()


# if __name__ == "__main__":

#     app = L.LightningApp(SlackRootFlow())
