import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

app = App(token=os.getenv("bot_token"))


@app.message("hi")
def hello(message, say):
    say(f"hello <@{message['user']}>!")

# start
if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("app_token")).start()