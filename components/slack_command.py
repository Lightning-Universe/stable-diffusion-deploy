import os

import lightning as L

from .slack_api import app as api


class SlackCommandWork(L.LightningWork):
    """
    class SlackRootFlow(L.LightningFlow):
        def __init__(self):
            super().__init__()
            self.slack_work = SlackCommandWork()

        def run(self):
            self.slack_work.run()
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self, inference_server_url: str, *args, **kwargs) -> None:
        print("starting Slack Listener")
        api.url = inference_server_url
        api.run(host=self.host, port=self.port)
