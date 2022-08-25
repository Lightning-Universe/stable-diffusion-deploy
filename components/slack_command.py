import os

import lightning as L


class SlackCommandListener(L.LightningWork):
    """
    To run this components:

    Step 1: Create a Slack App by logging in to https://api.slack.com

    Step 2: Copy the "bot token" and "signing token" from Slack App settings

    Step 3: Implement the `handle_command` function in `_slack_api.py` module

    class SlackRootFlow(L.LightningFlow):
        def __init__(self):
            super().__init__()
            self.slack_work = SlackCommandListener()

        def run(self):
            self.slack_work.run()
    """

    def __init__(self, signing_secret=None, bot_token=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if signing_secret:
            os.environ["SIGNING_SECRET"] = signing_secret
        if bot_token:
            os.environ["BOT_TOKEN"] = bot_token

    def run(self, inference_server_url: str, *args, **kwargs) -> None:
        from ._slack_api import app as api

        print("starting Slack Listener")
        api.url = inference_server_url
        api.run(host=self.host, port=self.port)
