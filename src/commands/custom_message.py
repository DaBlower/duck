# just duplicate this for new commands
import os
import logging
import datetime

program_name = "custom_message" # change this to the name of the command

# App variables for main script to set
app = None
bot_user_id = None

# Create logger
logger = logging.getLogger(program_name)

operators = None

def custom_message_handler(ack, respond, command):
    ack()
    name = "/sticky-note"

    channel_id = command["channel_id"]
    user_id = command["user_id"]
    args = command["text"].split(" ") # action, rest

    if user_id not in operators:
        respond(text="You need to be an operator of this bot to use this command :(", response_type="ephemeral")
        logger.info(f"User {user_id} used tried to use command {name} in {channel_id} without sufficient permissions")
        return
    
    if len(args) < 1 or len(args) > 3:
        respond(text="Usage: `/custom-message <message> <pfp link (optional)> <name of the bot (optional)>`", response_type="ephemeral")
        return

    message = args[0]
    
    pfp = (args[1] if args[1] else None)

    username = (args[2] if args[2] else None)

    app.client.chat_postMessage(channel=channel_id, icon_url=pfp if pfp else None, username=username if username else None, markdown_text=message)
    return

def initialise_custom_message(slack_app):
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
    app.command("/custom_message")(custom_message_handler)