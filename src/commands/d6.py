# a command that rolls a dice!
import os
import logging
import datetime
import random

program_name = "d6" # change this to the name of the command

# App variables for main script to set
app = None
bot_user_id = None

# Create logger
logger = logging.getLogger(program_name)

random.seed()

def d6(ack, respond, command):
    ack()

    channel_id = command["channel_id"]
    user_id = command["user_id"]
    args = command["text"].split(" ")
    num = random.randint(1,6)

    if args[0].lower() == "true":
        respond(text=f"<@{user_id}> rolled a {num}!", response_type="in_channel")
        logging.info(f"<@{user_id}> rolled a {num} in {channel_id}! (in_channel)")
    else:
        respond(text=f"you rolled a {num}!", response_type="ephemeral")
        logging.info(f"<@{user_id}> rolled a {num} in {channel_id}! (ephemeral)")


def initialise_d6(slack_app):
    global app, bot_user_id
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
    
    logger.info(f"{program_name} initialised")
    
    # Register command handler
    app.command("/d6")(d6)