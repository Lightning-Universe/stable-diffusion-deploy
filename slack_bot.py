from ast import arg
import slack
from flask import request, Response
from slackeventsapi import SlackEventAdapter
import os
from flask import Flask
from concurrent.futures import ThreadPoolExecutor
import threading
from flask import send_file

from dotenv import load_dotenv

load_dotenv(".env")

pool = ThreadPoolExecutor()
app = Flask(__name__)

slack_events_adapter = SlackEventAdapter(os.environ["SIGNING_SECRET"],"/slack/events", app)

client = slack.WebClient(token=os.environ["BOT_TOKEN"])

# client.chat_postMessage(channel="#dev-bot", text="Hi there!")

BOT_ID = client.api_call("auth.test")["user_id"]

def random(data):
    channel_id = data.get("channel_id")
    text = data.get("text")
    print(channel_id, text)
    client.files_upload(channels=channel_id, title=text, file="./assets/demo.png")
    # client.files_upload(channels="#dev-bot", title="something random", file="./assets/demo.png")

@app.route("/dream",methods=["post", "get"])
def dream():
    data = request.form
    print(data.keys())
    channel_id = data.get("channel_id")
    text = data.get("text")
    print(text)
    # th = threading.Thread(target=client.files_upload, kwargs=dict(channels=channel, title=text, file="./assets/demo.png"))
    th = threading.Thread(target=random, args=[data])
    th.start()
    return Response(), 200


if __name__=="__main__":
    app.run(debug=True, port=3000)
