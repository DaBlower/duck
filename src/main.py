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
from commands import ping
from modules import create_fingerprint
import message_handler

import logging, datetime

logger = logging.getLogger("main")

def main():
    load_dotenv()

    machine_id = create_fingerprint.host_fingerprint()
    print(f"Machine ID: {machine_id}")

    os.environ["machine_id"] = machine_id

    app = App(token=os.getenv("bot_token"))
    try:
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


    # logging
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    log_dir = os.path.join(project_root, "logs", "main")
    os.makedirs(log_dir, exist_ok=True)

    # Create specific logger for this command
    logger = logging.getLogger("main")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create file handler
    log_file = os.path.join(log_dir, f"{datetime.datetime.now().strftime('%Y-%m-%d')}.log")
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


if __name__ == "__main__":
    main()