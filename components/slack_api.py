import os
import threading
from concurrent.futures import ThreadPoolExecutor

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
    th = threading.Thread(
        target=client.files_upload,
        kwargs=dict(channels=channel_id, title=prompt, file="./assets/demo.png"),
    )
    th.start()


@app.route("/dream", methods=["post", "get"])
def handle_dream():
    data = request.form
    post_dream(data)
    return Response(), 200


if __name__ == "__main__":
    app.run(debug=True, port=3000)
