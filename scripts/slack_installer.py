"""This script is used to deploy Slack Oauth API separately."""
import json
import os

import lightning as L
import requests
from slack_command_bot import SlackCommandBot


class SlackInstaller(SlackCommandBot):
    SHEET_API_URL = os.environ.get("SHEET_API_URL")

    def handle_command(self):
        return "Dummy Method"

    def save_new_workspace(self, team_id, bot_token):
        data = [{"team_id": team_id, "bot_token": bot_token}]
        data = json.dumps(data)
        response = requests.post(self.SHEET_API_URL, data=data)
        response.raise_for_status()


class SlackRootFlow(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self.slack_bot = SlackInstaller()
        self.printed = False

    def run(self):
        self.slack_bot.run()
        if self.slack_bot.url and not self.printed:
            print(self.slack_bot.url)
            self.printed = True


if __name__ == "__main__":
    app = L.LightningApp(SlackRootFlow())
