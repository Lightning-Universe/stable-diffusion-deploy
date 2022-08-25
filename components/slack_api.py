import base64
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import requests
import slack
from dotenv import load_dotenv
from flask import Flask, Response, request
from slackeventsapi import SlackEventAdapter

load_dotenv(".env")

pool = ThreadPoolExecutor()
app = Flask(__name__)

slack_events_adapter = SlackEventAdapter(
    os.environ["SIGNING_SECRET"], "/slack/events", app
)

client = slack.WebClient(token=os.environ["BOT_TOKEN"])
BOT_ID = client.api_call("auth.test")["user_id"]


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

    with open("generated.png", "w") as fh:
        image_str = generated_images[0]
        print(image_str)
        fh.write(image_str)

    client.files_upload(channels=channel_id, title=prompt, file="./generated.png")


@app.route("/dream", methods=["post", "get"])
def handle_dream():
    data = request.form
    post_dream(data)
    return Response(), 200


if __name__ == "__main__":
    app.run(debug=True, port=3000)
