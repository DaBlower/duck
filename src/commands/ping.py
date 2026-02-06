# just duplicate this for new commands
import os
import logging
import datetime
import json

import subprocess, re, sys

program_name = "ping" # change this to the name of the command

# App variables for main script to set
app = None
bot_user_id = None

# Create logger
logger = logging.getLogger(program_name)

maintainer = None

def ping_slack():
    # platform specific
    count_flag = "-n" if sys.platform.startswith("win") else "-c"

    cmd = ["ping", count_flag, "1", "slack.com"]


    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=2
    )

    try:
        result.check_returncode()
    except subprocess.CalledProcessError:
        return None
    
    match = re.search(r"time[=<]\s*([\d.]+)\s*ms", result.stdout) # regex made by ai because i suck at regex
    if not match:
        return None

    return float(match.group(1))

def ping_handler(ack, respond, command, client):
    ack()

    channel_id: str = command["channel_id"]
    user_id: str = command["user_id"]
    text: str = command["text"]

    ping = ping_slack()
    if ping is not None:

        respond(f"pong! ~{ping:.1f}")
    else:
        respond(f"no match :c - dm <@{maintainer}>")

def initialise_ping(slack_app):
    global app, bot_user_id
    global maintainer
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
    app.command("/pingo")(ping_handler)

    maintainer = os.getenv("maintainer")