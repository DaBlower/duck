# just duplicate this for new commands
import os
import logging
import datetime
import time
import json
import ntplib

program_name = "ping" # change this to the name of the command

# App variables for main script to set
app = None
bot_user_id = None

# Create logger
logger = logging.getLogger(program_name)

def ping_handler(ack, respond, command, client):
    ack()

    channel_id: str = command["channel_id"]
    user_id: str = command["user_id"]
    text: str = command["text"]


    print(json.dumps(command, indent=2))
    # slack_ts = float(command["command_ts"])
    # now = time.time()

    # latency_ms = (now - slack_ts) * 1000

    # respond(f"pong! {latency_ms:.0f}ms")
    result = client.chat_postMessage( # post the message first, then edit it later when we get the timestamp from this (result["ts"])
        channel = channel_id,
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "pong!\nping?"
                }
            },
        ]
    )

    ts = result["ts"]
    float_ts = float(ts)

    epoch = float(server_time())

    approx_ping = (epoch-float_ts) * 1000

    time.sleep(0.75)

    client.chat_update( # now we update it?
        channel = channel_id,
        ts = ts,
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"pong!\n{approx_ping}"
                }
            }
        ]
    )


NTP_OFFSET = None
NTP_LAST_SYNC = 0
NTP_SERVER = ""

def server_time():
    global NTP_OFFSET, NTP_LAST_SYNC

    now = time.time()

    try:
        if NTP_OFFSET is None or now - NTP_LAST_SYNC > 300:
            client = ntplib.NTPClient()
            response = client.request(NTP_SERVER, version=3)
            NTP_OFFSET = response.tx_time - now
            NTP_LAST_SYNC = now
    except Exception as e:
        return now

    return now+NTP_OFFSET

def initialise_ping(slack_app):
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
    app.command("/pingo")(ping_handler)

    NTP_SERVER = os.getenv("ntp_server")