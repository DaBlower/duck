# a command that rolls a dice!
import os
import logging
import datetime
import random

program_name = "dx" # change this to the name of the command

# App variables for main script to set
app = None
bot_user_id = None

# Create logger
logger = logging.getLogger(program_name)

random.seed()

def dx(ack, respond, command):
    ack()

    channel_id = command["channel_id"]
    user_id = command["user_id"]
    args = command["text"].split(" ")

    # check args
    if len(args) < 1 or not args[0].strip():
        logger.warning(f"User {user_id} ran /dx in {channel_id} with args {command["text"]}")
        respond(text="Usage: `/dx <sides> [post in channel (true/false)]`, you need to specify the number of sides!", response_type="ephemeral")
        return
    
    sides_str = args[0]
    try:
        sides = int(sides_str)
        if sides < 1:
            raise ValueError("Sides must be positive!")
        if sides > 9999999:
            respond(text=f"{sides} is way too high :heavysob: please decrease it", response_type="ephemeral")
            logger.warning(f"user {user_id} tried to run /dx with {sides} sides in channel {channel_id}, which is way too much. pls find them :D")
            return
        num = random.randint(1,sides)
    except Exception as e:
        logger.error(f"Failed to cast sides to int (sides = {sides_str}), ran by {user_id} in channel {channel_id}: {e}")    
        respond(text=f"{sides_str} is not a valid integer", response_type="ephemeral")
        return


    public_flag = len(args) > 1 and args[1].strip().lower() == "true"

    if public_flag:
        respond(text=f":dice-roll: <@{user_id}> rolled a {num}!", response_type="in_channel")
        logger.info(f"<@{user_id}> rolled a {num} in {channel_id}! (in_channel)")
    else:
        respond(text=f":dice-roll: you rolled a {num}!", response_type="ephemeral")
        logger.info(f"<@{user_id}> rolled a {num} in {channel_id}! (ephemeral)")


def initialise_dx(slack_app):
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
    app.command("/dx")(dx)