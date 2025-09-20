import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# import modules and commands
from commands import sticky
from modules import check_manager

def main():
    load_dotenv()

    app = App(token=os.getenv("bot_token"))

    check_manager.initialise_check_manager()
    sticky.initialise_sticky_command(app)

    handler = SocketModeHandler(app, os.getenv("app_token"))
    handler.start()

if __name__ == "__main__":
    main()