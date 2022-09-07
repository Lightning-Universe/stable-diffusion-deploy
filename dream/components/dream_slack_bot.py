import base64
import json
import os
import tempfile
import threading

import requests
import slack
from flask import Response, request
from slack_command_bot import SlackCommandBot


class DreamSlackCommandBot(SlackCommandBot):
    def __init__(
        self,
        command="/dream",
        signing_secret=None,
        bot_token=None,
        slack_client_id=None,
        client_secret=None,
        *args,
        **kwargs,
    ):
        super().__init__(command, signing_secret, bot_token, slack_client_id, client_secret, *args, **kwargs)
        self.inference_url = None
        self.API_URL = os.environ.get("SHEET_API_URL")

    def handle_command(self):
        data: dict = request.form
        prompt = data.get("text")
        team_id = data.get("team_id")
        response = requests.get(f"{self.API_URL}?search=" + json.dumps({"team_id": team_id}))
        try:
            bot_token = response.json()[0]["bot_token"]
        except IndexError:
            return Response(f"Bot Token not found for for team={team_id}", status=401)
        client = slack.WebClient(token=bot_token)

        th = threading.Thread(target=post_dream, args=[self.inference_url, client, data], daemon=True)
        th.start()
        msg = f":zap: Generating image for prompt: _{prompt}_ :zap:. (This public version of the app may run slow. Follow this tutorial to run your own faster version of the app in your workspace https://youtu.be/nmoQAVbyu-U"  # noqa: E501
        return msg, 200

    def save_new_workspace(self, team_id, bot_token):
        data = [{"team_id": team_id, "bot_token": bot_token}]
        data = json.dumps(data)
        response = requests.post(self.API_URL, data=data)
        response.raise_for_status()

    def run(self, inference_url, *args, **kwargs) -> None:
        self.inference_url = inference_url
        return super().run(*args, **kwargs)


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
    payload = {
        "dream": prompt,  # represents text of 'Enter the text prompt' Textbox component
        "num_images": 1,  # represents selected choice of 'Number of images' Radio component
        "image_size": 512,  # represents selected choice of 'Image Size' Radio component
    }
    payload = json.dumps(payload)
    response = requests.post(inference_url + "/api/predict", data=payload)
    print(response.status_code)
    response.raise_for_status()
    generated_images: list = response.json()
    with tempfile.NamedTemporaryFile() as file:
        save_base64(generated_images[0], file.name)
        client.files_upload(channels=channel_id, title=prompt, file=file.name)
