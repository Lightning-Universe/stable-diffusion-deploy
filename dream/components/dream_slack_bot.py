import base64
import json
import os
import threading

import lightning as L
import requests
import slack
from flask import Flask, request
from slack_command_bot import SlackCommandBot


class DreamSlackCommandBot(SlackCommandBot):
    def handle_command(self, client: slack.WebClient):
        data: dict = request.form
        prompt = data.get("text")
        th = threading.Thread(target=post_dream, args=[data])
        th.start()
        msg = f":zap: Generating image for prompt: _{prompt}_ :zap: . (This is a public version of this app and might run slow, run this app on your own lightning.ai account for faster speeds.)"
        return msg, 200


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


def post_dream(flask_app: Flask, client: slack.WebClient, data: dict):
    channel_id = data.get("channel_id")
    prompt = data.get("text")
    payload = {
        "data": [
            prompt,  # represents text of 'Enter the text prompt' Textbox component
            1,  # represents selected choice of 'Number of images' Radio component
            512,  # represents selected choice of 'Image Size' Radio component
        ]
    }
    payload = json.dumps(payload)
    response = requests.post(flask_app.url + "/api/predict", data=payload)
    print(response.status_code)
    response.raise_for_status()
    generated_images: list = response.json()["data"][0]
    save_base64(generated_images[0], "./generated.png")
    client.files_upload(channels=channel_id, title=prompt, file="./generated.png")
