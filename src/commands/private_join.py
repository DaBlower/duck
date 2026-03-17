# just duplicate this for new commands
import os
import logging
import datetime

# for intellisense, also do client: WebClient for the handler
from slack_bolt.context.respond import Respond
from slack_sdk.web.client import WebClient 

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

program_name = "private_join" # change this to the name of the command

# App variables for main script to set
app = None
bot_user_id = None

# Create logger
logger = logging.getLogger(program_name)

blacklisted_users = None
priv_channel_id = None
op_user = None

def join_command(ack, respond, command, client):
    ack()

    user_id = command["user_id"]

    dm = client.conversations_open(users=op_user)
    dm_channel_id = dm["channel"]["id"]

    if check_blacklist(user_id):
        app.client.chat_postMessage(
            channel=dm_channel_id,
            text=f"blacklisted user <@{user_id}> tried to request"
        )

        return
    
    app.client.chat_postMessage(
        channel=dm_channel_id,
        text=f"<@{user_id}>",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<@{user_id}> wants to join"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "yes",
                            "emoji": True
                        },
                        "style": "primary",
                        "value": f"{user_id}",
                        "action_id": "approve-button"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "no",
                            "emoji": True
                        },
                        "style": "danger",
                        "value": f"{user_id}",
                        "action_id": "decline-button"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "blacklist",
                            "emoji": True
                        },
                        "value": f"{user_id}",
                        "action_id": "blacklist-button"
                    }
                ]
            }
        ]
    )

    respond(f"hey, i've sent your request and you might be let in soon :3", response_type="ephemeral")

def approve_btn(ack, body, client, action):
    ack()

    channel_id = body["container"]["channel_id"]
    requester = action["value"]
    message_ts = body["container"]["message_ts"]

    client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text=f"Request by <@{requester}> approved"
    )

    client.conversations_invite(
        channel=f"{priv_channel_id}",
        users=f"{requester}"
    )

def blacklist_btn(ack, body, client, action):
    ack()

    channel_id = body["container"]["channel_id"]
    requester = action["value"]
    message_ts = body["container"]["message_ts"]

    client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text=f"Blacklisted <@{requester}>"
    )

    try:
        add_to_blacklist(requester)
    except Exception as e:
        logger.info(f"Failed to add user to blacklist: {e}")

def add_to_blacklist(user_id):
    user = str(user_id)

    blacklist_path = os.path.join(project_root, "db", "blacklist.txt")

    exists = False
    if os.path.exists(blacklist_path):
        with open(blacklist_path, "r") as f:
            if user in f.read().splitlines():
                exists = True

    if not exists:
        with open(blacklist_path, "a") as f:
            f.write(f"{user_id}\n")

def check_blacklist(user_id):
    print("blacklist")
    user = str(user_id)
        
    blacklist_path = os.path.join(project_root, "db", "blacklist.txt")

    exists = False
    if os.path.exists(blacklist_path):
        with open(blacklist_path, "r") as f:
            if user in f.read().splitlines():
                exists = True

    return exists

def decline_btn(ack, body, client, action):
    ack()

    channel_id = body["container"]["channel_id"]
    requester = action["value"]
    message_ts = body["container"]["message_ts"]

    client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text=f"Request by <@{requester}> declined"
    )

def initialise_join(slack_app):
    global app, bot_user_id, op_user, blacklisted_users, priv_channel_id
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
    
    op_user = os.getenv("op_user")
    priv_channel_id = os.getenv("priv_channel_id")

    logger.info(f"{op_user} is the op_user and #{priv_channel_id} is the private channel")
    logger.info(f"{program_name} initialised")
    
    # Register command handler
    app.command("/join-obobs-duck")(join_command)

    app.action("approve-button")(approve_btn)
    app.action("decline-button")(decline_btn)
    app.action("blacklist-button")(blacklist_btn)