# just duplicate this for new commands
import os
import re
import logging
import datetime

# for intellisense, also do client: WebClient for the handler
from slack_bolt.context.respond import Respond
from slack_sdk.web.client import WebClient 

program_name = "leave_channel" # change this to the name of the command

# App variables for main script to set
app = None
bot_user_id = None

operators = None

# Create logger
logger = logging.getLogger(program_name)

def leave_handler(ack, command, respond, body, client):
    ack()

    user_id = command["user_id"]
    channel = body["text"]

    if user_id not in operators:
        respond(text="You need to be an operator of this bot to use this command :(", response_type="ephemeral")
        logger.info(f"{user_id} tried to remove from {channel} without sufficient permissions")
        return


    logger.info(f"{user_id} tried to remove from {channel}")

    match = re.match(r"^<#([A-Z0-9]+)(?:\|[a-z0-9-_]+)?>$", channel)
    if not match:
        respond(f"{channel} is not a valid channel name", response_type="ephemeral")
        logger.info(f"{channel} is not a valid channel")
        return

    channel_id = match.group(1)

    # check if bot is in channel
    response = client.conversations_info(channel=channel_id)
    is_member = response["channel"]["is_member"]

    if not is_member:
        logger.info(f"bot is not a part of {channel}")
        respond(f"bot is not a part of {channel}", response_type="ephemeral")
        return

    try:
        client.conversations_leave(channel=channel_id)
    except Exception as e:
        respond("error while leaving")
        logger.info(f"error while leaving: {e}")
        return

    logger.info("left sucessfully")

    respond(f"left {channel}", response_type="ephemeral")

def initialise_leave(slack_app):
    global app, bot_user_id, operators
    app = slack_app
    bot_user_id = app.client.auth_test()["user_id"]

    # Set up logging
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
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
    
    operators = os.getenv("operators", "").split(",")
    operators = [user.strip() for user in operators if user.strip()]

    logger.info(f"{program_name} initialised")
    
    # Register command handler
    app.command("/oleave")(leave_handler)