import os, sys
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# import modules and commands
from commands import sticky
from commands import d6
from commands import dx
from commands import reply
from commands import custom_message
from commands import yubico_otp
from modules import check_manager
from commands import ping
import message_handler

def main():
    load_dotenv()

    app = App(token=os.getenv("bot_token"))
    try:
        check_manager.initialise_check_manager()
        sticky.initialise_sticky_command(app)
        d6.initialise_d6(app)
        dx.initialise_dx(app)
        yubico_otp.initalise_otp(app)
        custom_message.initialise_custom_message(app)
        reply.initalise_reply(app)
        message_handler.initialise_handler(app)
        ping.initialise_ping(app)

    except RuntimeError as e:
        sys.exit(2)


    handler = SocketModeHandler(app, os.getenv("app_token"))
    handler.start()

if __name__ == "__main__":
    main()