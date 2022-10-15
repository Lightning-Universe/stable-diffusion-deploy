import asyncio
import base64
import json
import logging
import os
import sys
import tempfile
import threading
import typing

import requests
import slack
import uvicorn
from asgiref.typing import ASGIApplication
from asgiref.wsgi import WsgiToAsgi
from flask import Flask, Response, request
from flask_cors import CORS
from lightning_app.storage.drive import Drive
from slack_command_bot import SlackCommandBot
from uvicorn.supervisors import ChangeReload, Multiprocess

from ..CONST import RATE_LIMIT_KEY
from ..utility.data_io import get_item, save_item


class MuseSlackCommandBot(SlackCommandBot):
    """The MuseSlackCommandBot."""

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.inference_url = None
        self.has_credentials = False
        self._slack_token: str = None
        self._secrets_drive: Drive = None
        self._server: uvicorn.Server = None

        self._SHEET_API_URL = os.environ.get("SHEET_API_URL")

    def _get_bot_token(self, team_id):
        if self._SHEET_API_URL:
            response = requests.get(f"{self._SHEET_API_URL}?search=" + json.dumps({"team_id": team_id}))
            bot_token = response.json()[0]["bot_token"]
        else:
            bot_token = self.bot_token
        return bot_token

    def handle_command(self):
        data: dict = request.form
        prompt = data.get("text")
        team_id = data.get("team_id")
        try:
            bot_token = self._get_bot_token(team_id)
        except IndexError:
            return Response(f"Bot Token not found for for team={team_id}", status=401)

        client = slack.WebClient(token=bot_token)
        th = threading.Thread(target=post_dream, args=[self.inference_url, client, data], daemon=True)
        th.start()
        msg = f":zap: Generating image for prompt: _{prompt}_ :zap:. (This public version of the app may run slow. Clone and run the app on your own Lightning AI account to enable the creation of your own Slackbot with customizable performance)"  # noqa: E501
        return msg, 200

    def save_new_workspace(self, team_id, bot_token):
        data = [{"team_id": team_id, "bot_token": bot_token}]
        data = json.dumps(data)
        response = requests.post(self._SHEET_API_URL, data=data)
        response.raise_for_status()

    def run(self, inference_url) -> None:
        if not inference_url:
            return

        self._get_credentials()
        self.inference_url = inference_url
        self.run_app()

    def run_app(self):
        app = Flask(__name__)
        CORS(app, resources={r"/add_credentials": {"origins": "*"}})

        if self.has_credentials:
            self.init_flask_app(app=app)
        else:
            self.register_credentials_endpoint(app=app)

        asgi_app = WsgiToAsgi(app)
        config = uvicorn.Config(app=asgi_app, host=self.host, port=self.port)

        print("starting Slack Command Bot")
        self.run_server(app=asgi_app, config=config)

    def register_credentials_endpoint(self, app: Flask):
        @app.route("/add_credentials", methods=["POST"])
        def add_secrets():
            if self.has_credentials:
                return "already have credentials"
            data: dict = request.get_json()
            self.assign_credentials(credentials=data)
            save_item(name="secrets", value=data, drive=self._secrets_drive)
            self.restart_server()
            return "success"

    def _get_credentials(self) -> bool:
        try:
            # try to get from env
            self.assign_credentials(credentials=os.environ)
            return True
        except BaseException:
            pass

        if not self._secrets_drive:
            self._secrets_drive = Drive(id="lit://secrets", component_name=self.__class__.__name__)
        credentials = get_item(name="secrets", drive=self._secrets_drive)
        if not credentials:
            return False

        try:
            self.assign_credentials(credentials=credentials)
            return True
        except BaseException as e:
            print(e)
            return False

    def assign_credentials(self, credentials: typing.Dict):
        self._signing_secret = credentials["SIGNING_SECRET"]
        self._bot_token = credentials["BOT_TOKEN"]
        self._slack_client_id = credentials["SLACK_CLIENT_ID"]
        self._client_secret = credentials["CLIENT_SECRET"]
        self._slack_token = credentials["SLACK_TOKEN"]

        self.has_credentials = True

    def restart_server(self):
        self._server.force_exit = True
        self._server.lifespan = "on"
        asyncio.run(self._server.shutdown())
        threading.Thread(target=self.run_app, daemon=False).start()

    def run_server(self, app: typing.Union[ASGIApplication, str], config: uvicorn.Config = None) -> None:
        """copy of uvicorn.run."""

        server = uvicorn.Server(config=config)

        self._server = server

        if (config.reload or config.workers > 1) and not isinstance(app, str):
            logger = logging.getLogger("uvicorn.error")
            logger.warning("You must pass the application as an import string to enable 'reload' or " "'workers'.")
            sys.exit(1)

        if config.should_reload:
            sock = config.bind_socket()
            ChangeReload(config, target=server.run, sockets=[sock]).run()
        elif config.workers > 1:
            sock = config.bind_socket()
            Multiprocess(config, target=server.run, sockets=[sock]).run()
        else:
            server.run()
        if config.uds:
            os.remove(config.uds)  # pragma: py-win32

        if not server.started and not config.should_reload and config.workers == 1:
            sys.exit(uvicorn.main.STARTUP_FAILURE)


def save_base64(b64_image, filename="generate.png"):
    # open file with base64 string data
    encoded_data = bytes(b64_image, "utf-8")
    encoded_data = encoded_data.replace(b"data:image/png;base64,", b"")

    # decode base64 string data
    decoded_data = base64.b64decode(encoded_data)
    # write the decoded data back to original format in  file
    img_file = open(filename, "wb")
    img_file.write(decoded_data)
    img_file.close()


def post_dream(inference_url: str, client: "slack.WebClient", data: dict):
    channel_id = data.get("channel_id")
    prompt = data.get("text")
    headers = {
        "accept": "application/json",
        "x-api-key": RATE_LIMIT_KEY,
        # Already added when you pass json= but not when you pass data=
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,  # represents text of 'Enter the text prompt' Textbox component
        "high_quality": True,
    }
    payload = json.dumps(payload)
    response = requests.post(inference_url + "/api/predict", data=payload, headers=headers)
    response.raise_for_status()
    generated_image: str = response.json()["image"]
    with tempfile.NamedTemporaryFile() as file:
        save_base64(generated_image, file.name)
        client.files_upload(channels=channel_id, title=prompt, file=file.name)
