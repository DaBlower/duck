# just duplicate this for new commands
import os
import logging
import datetime
import socket, time

from slack_bolt.context.respond import Respond
from slack_sdk.web.client import WebClient


import subprocess, re, sys

program_name = "ping" # change this to the name of the command

# App variables for main script to set
app = None
bot_user_id = None

# Create logger
logger = logging.getLogger(program_name)

maintainer = None

def tcp_ping(host="slack.com", port=443, timeout=2):
    start = time.time()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return (time.time() - start) * 1000
    except Exception as e:
        return None

def api_call(client: WebClient):
    try:
        start = time.time()
        client.api_test()
        latency = (time.time() - start) * 1009
    except Exception as e:
        return None

    return latency

def ping_handler(ack, respond: Respond, command: dict, client: WebClient):
    ack()

    channel_id: str = command["channel_id"]
    user_id: str = command["user_id"]
    text: str = command["text"]

    ping = tcp_ping()
    api_ping = api_call(client)
    if ping is not None and api_ping is not None:
        respond(f"pong!\n~{ping:.1f}ms (tcp)\n~{api_ping:.1f}ms (api) :D")
    else:
        respond(f"error :c - dm <@{maintainer}>")

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