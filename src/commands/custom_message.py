# just duplicate this for new commands
import os
import logging
import datetime
from slack_sdk.errors import SlackApiError

program_name = "custom_message" # change this to the name of the command

# App variables for main script to set
app = None
bot_user_id = None

# Create logger
logger = logging.getLogger(program_name)

operators = None

def custom_message_handler(ack, respond, command):
    ack()
    name = "/custom-message"

    channel_id: str = command["channel_id"]
    user_id: str = command["user_id"]
    text: str = command["text"]

    logger.info(f"new /custom-message command ran by {user_id} in {channel_id}, contents: {text}")

    # defaults so this doesn't break when /self isn't true
    username = None
    pfp = None

    if user_id not in operators:
        respond(text="You need to be an operator of this bot to use this command :(", response_type="ephemeral")
        logger.info(f"User {user_id} used tried to use command {name} in {channel_id} without sufficient permissions")
        return
    
    if len(text) < 1:
        respond(text='Usage: `/custom-message <message> (include /self to copy your pfp and name)`", response_type="ephemeral')
        return


    # check if \self is used for username, and copy the users pfp and username    
    if "/self" in text:
        message = text.replace("/self", "").strip()
        selfMsg = True
        logger.info("/self is in the message")

        try:
            response = app.client.users_profile_get(user = user_id) # get data
            profile = response["profile"]
            username = profile.get("display_name")
            pfp = profile.get("image_192")
            logger.info(f"/self profile loaded for {user_id}, username={username}, has_pfp={bool(pfp)}")
        except SlackApiError as e:
            logger.info(f"Slack api error when loading profile: {e}")

    else:
        message = text

    try:
        app.client.chat_postMessage(channel=channel_id, username=username if username else None, icon_url=pfp if pfp else None, text=message)
    except SlackApiError as e:
        logger.error(f"Error sending message: {e}")

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
    app.command("/custom-message")(custom_message_handler)