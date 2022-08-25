import base64
import json
import os
import threading

import requests
import slack
from dotenv import load_dotenv
from flask import Flask, request
from slackeventsapi import SlackEventAdapter

load_dotenv(".env")

app = Flask(__name__)

slack_events_adapter = SlackEventAdapter(
    os.environ["SIGNING_SECRET"], "/slack/events", app
)

client = slack.WebClient(token=os.environ["BOT_TOKEN"])
BOT_ID = client.api_call("auth.test")["user_id"]


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


def post_dream(data: dict):
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
    response = requests.post(app.url + "/api/predict", data=payload)
    print(response.status_code)
    response.raise_for_status()
    generated_images: list = response.json()["data"][0]
    save_base64(generated_images[0], "./generated.png")
    client.files_upload(channels=channel_id, title=prompt, file="./generated.png")


@app.route("/dream", methods=["post", "get"])
def handle_command():
    data: dict = request.form
    prompt = data.get("text")
    th = threading.Thread(target=post_dream, args=[data])
    th.start()
    msg = f":zap: Generating image for prompt: _{prompt}_ :zap: . (This is a public version of this app and might run slow, run this app on a private cloud for faster inference. Learn more at lightning.ai)"
    return msg, 200


if __name__ == "__main__":
    app.run(debug=True, port=3000)
