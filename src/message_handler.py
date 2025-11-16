# just duplicate this for new commands
import os
import re
import logging
import datetime

from commands import sticky, yubico_otp

YUBICO_MODHEX = r"[cbdefghijklnrtuv]" # modhex for the otp command

scripts = {
    "sticky": {
        "function": sticky.check_sticky,
        "regex": re.compile(r".*", re.DOTALL)
    },

    "yubico_otp": {
        "function": yubico_otp.new_msg,
        "regex": re.compile(rf"^{YUBICO_MODHEX}{{44}}$")
    }
}


program_name = "message_handler" # change this to the name of the command

# App variables for main script to set
app = None
bot_user_id = None

# Create logger
logger = logging.getLogger(program_name)


def handle_message(message, client):
    logger.info(f"New message! message: {message}")
    for name, data in scripts.items():
        func = data.get("function")
        regex = data.get("regex")
        body = message.get("text", "")

    
        if regex.fullmatch(body):
            logger.info(f"Message fullmatches with {name} ({func}), actual text: {body}")
            func(message, client)
    return None



def initialise_handler(slack_app):
    global app, bot_user_id
    app = slack_app
    bot_user_id = app.client.auth_test()["user_id"]

    # Set up logging
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    log_dir = os.path.join(project_root, "logs", program_name)
    os.makedirs(log_dir, exist_ok=True)

    # Create specific logger for this command
    logger = logging.getLogger(program_name)
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
    
    logger.info(f"{program_name} initialised")
        
    # Register message handler
    app.message()(handle_message)
