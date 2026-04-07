import requests
import subprocess
import platform
import re
import time
import threading
import os
import logging
import datetime

program_name = "kuma_heartbeat"

# App variables for main script to set
app = None
kuma_url = None

# Create logger
logger = logging.getLogger(program_name)

def send_heartbeat():
    time.sleep(10)
    while True:
        ping = get_ping()
        try:
            if ping:
                requests.get(kuma_url + '?status=up&msg=OK&ping=' + str(ping), timeout=5)
            else:
                requests.get(kuma_url + '?status=up&msg=OK', timeout=5)
        except Exception as e:
            logger.error(f"Failed to send Kuma heartbeat: {e}")

        time.sleep(55)

def get_ping():
    param = '-c' if platform.system().lower() != 'windows' else '-n'
    command = ['ping', param, '1', '1.1.1.1']

    try:
        output = subprocess.check_output(command).decode().strip()

        search = re.search(r'time=([\d.]+)\s*ms', output)
        if search:
            return int(float(search.group(1)))
        else:
            return None
    except Exception as e:
        logger.error(f"Failed to get ping: {e}")
        return None

def initialise_kuma_heartbeat(slack_app):
    global app, bot_user_id, kuma_url
    app = slack_app

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

    kuma_url = os.getenv("KUMA_URL")
    if not kuma_url:
        logger.error("KUMA_URL env not set")

    threading.Thread(target=send_heartbeat, daemon=True).start()

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logger.info(f"{program_name} initialised")