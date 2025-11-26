import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("bot_token")
CHANNEL_ID = "C09ETD04JH1"  # Replace with your channel ID

def send_slack_message(channel: str, text: str):
    url = "https://slack.com/api/chat.postMessage"

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    }

    payload = {
        "channel": channel,
        "text": text,
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    data = response.json()

    if not data.get("ok"):
        raise Exception(f"Slack API error: {data}")

    return data

if __name__ == "__main__":
    result = send_slack_message(CHANNEL_ID, 'this was used during the slack outage')
    print(result)
