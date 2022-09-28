<div align="center">
    <h1>
        Lightning Muse App
    </h1>
    <img src="https://pl-flash-data.s3.amazonaws.com/assets_lightning/docs/images/logos/lightning-ai.png" width="400px">

<div align="center">

<p align="center" style="color:grey">Powered by <a href="https://stability.ai/blog/stable-diffusion-public-release">Stable Diffusion</a></p>

<p align="center">
  <a href="#getting-started">Getting Started</a> •
  <a href="https://www.lightning.ai/">Lightning AI</a> •
  <a href="https://lightning.ai/apps">Lightning Apps Gallery</a>
</p>

[![ReadTheDocs](https://readthedocs.org/projects/pytorch-lightning/badge/?version=stable)](https://lightning.ai/lightning-docs/)
[![Slack](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://www.pytorchlightning.ai/community)
[![license](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/Lightning-AI/lightning/blob/master/LICENSE)

</div>
</div>

______________________________________________________________________

# Lightning Muse App

\[TODO\]

## Getting started

```bash
conda create --name muse_app python=3.8
conda activate muse_app

git clone https://github.com/Lightning-AI/LAI-Muse-App.git
cd LAI-Muse-App
pip install -r requirements.txt
pip install -e .

## To run the app locally
python -m lightning run app app.py

## To run the app on the cloud to share it with your peers and users
python -m lightning run app app.py --cloud
```

## About this Lightning App

This Lightning App is powered by Stable Diffusion to generate images via text prompts.
This application is fairly simple already showcases the following features of Lightning Framework:

- Multi-tenant Frontend & Backend application architecture
- UI written in React
- Backend serving REST API (with FastAPI)
- Load Balancer to handle requests and serve them across multiple Lightning Works
- Environment variables to parametrize execution environment

<details>
<summary><b><u>Integrate with Slack Bot</u></b></summary>

You can integrate this app in your Slack Workspace and send art in slack channels.

This app uses the [Slack Command Bot Component](https://github.com/Lightning-AI/LAI-slack-command-bot-Component) for to
interact with Slack command.

[![Watch the video](https://img.youtube.com/vi/KfQcXzWFR9I/default.jpg)](https://youtu.be/KfQcXzWFR9I)

### Steps to create the Slack Command Bot

**Step 1:**
Goto https://api.slack.com and create an app.

**Step 2:**
Copy the following tokens and secrets from the Slack API settings by going to https://api.slack.com/apps. These tokens
have to be passed either as argument or environment variable to [SlackCommandBot](https://github.com/Lightning-AI/LAI-slack-command-bot-Component/blob/main/slack_command_bot/component.py#L18) class.

<details>
  <summary>Required Token name and environment variables: </summary>

- Client ID (SLACK_CLIENT_ID)
- Client Secret (CLIENT_SECRET)
- Signing Secret (SIGNING_SECRET)
- Bot User OAuth Token (BOT_TOKEN)
- App-Level Token (SLACK_TOKEN)

</details>

**Step 3:**

Implement the `SlackCommandBot.handle_command(...)` method the way you want to interact with the commands.
The return value will be shown only to you.

> ![](./assets/slack-ss.png)

**Step 4:** (optional)

If you want your slack app to be distributable to public then you need to
implement `SlackCommandBot.save_new_workspace(...)` which should save `team_id` and its corresponding `bot_token` into a
database.

During the `handle_command(...)` method you will need to fetch `bot_token` based on the received `team_id`.

</details>

## Credits

\[TODO\]
