import os, logging, datetime, random

program_name = "reply" # change this to the name of the command

# App variables for main script to set
app = None
bot_user_id = None

# Create logger
logger = logging.getLogger(program_name)

TARGET_CHANNELS = None # channels for the bot to reply in
sarc_users = []

random.seed()

def new_interaction(event, say):
    channel_id = event.get("channel", "")
    user_id = event.get("user", "")
    thread_ts = event.get("thread_ts", event.get("ts", ""))
    text = event.get("text", "")

    logger.info(f"Received message in channel {channel_id}, ts {thread_ts} from user {user_id}: {text}")


    # ignore messages from the bot itself
    if user_id == bot_user_id:
        logger.info("Ignoring message from bot")
        return

     # ignore messages not in target channels
    if channel_id not in TARGET_CHANNELS:
        logger.info(f"Ignoring message in wrong channel (expected {TARGET_CHANNELS}, got {channel_id})")
        return
    if user_id not in sarc_users:
        say(text=pick_reply(False), thread_ts=thread_ts)
    else:
        say(text=pick_reply(True), thread_ts=thread_ts)
    

def pick_reply(sarc: bool = False): # i cant get used to not static typing loll
    rand = random.randrange(0,3)
    if sarc == True:
        logger.info("this is a sarcastic user")
        responses = ["what do you want :very-mad::mad_ping_sock:", "how can i NOT help you?", "leave me alone", "silence, peasant"]
    else:
        logger.info("this is not a sarcastic user")
        responses = ["hello nice person!", "how can i help you?", "nice to meet you (too)", "hello! are you having a good day?"]
    return responses[rand]

def initalise_reply(slack_app):
    global app, bot_user_id, TARGET_CHANNELS, sarc_users
    app = slack_app
    bot_user_id = app.client.auth_test()["user_id"]

    # load envs
    TARGET_CHANNELS = os.getenv("CHANNEL_ID", "").split(",")
    TARGET_CHANNELS = [channel.strip() for channel in TARGET_CHANNELS if channel.strip()]

    # Set up logging
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    log_dir = os.path.join(project_root, "logs", program_name)
    os.makedirs(log_dir, exist_ok=True)

    # Create specific logger for this command
    logger = logging.getLogger(program_name)
    logger.setLevel(logging.DEBUG)
    
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

    # users that the bot will reply in a not as kind way when mentioned >:)
    sarc_users = os.getenv("SARC_USERS", None)
    if not sarc_users:
        logger.warning("You haven't set sarcastic users in your env yet! for now, we will respond as if everyone is normal")
        sarc_users = ""

    sarc_users = sarc_users.split(",")
    sarc_users = [channel.strip() for channel in sarc_users if channel.strip()]

    logger.info(f"{program_name} initialised")