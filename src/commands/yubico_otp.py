import os, re, requests, secrets, base64, hashlib, hmac, urllib.parse, logging, datetime

program_name = "yubico-otp" # change this to the name of the command

# App variables for main script to set
app = None
bot_user_id = None

# Create logger
logger = logging.getLogger(program_name)

YUBICO_CLIENT_ID = os.getenv("YUBICO_CLIENT_ID")
YUBICO_SECRET_KEY = os.getenv("YUBICO_SECRET_KEY")
TARGET_CHANNEL = os.getenv("CHANNEL_ID")

YUBIKEY_REGEX = re.compile(r"\b[cbdefghijklnrtuv]{44}\b") # regex is crazy

def new_msg(message, client):
    channel_id = message.get("channel", "")
    user_id = message.get("user", "")
    text = message.get("text", "")
    subtype = message.get("subtype", "")

    logger.info(f"Received message in channel {channel_id} from user {user_id}: {text} (subtype: {subtype})")

    # ignore messages with no user
    if not user_id:
        logger.info("Ignoring message without user")
        return

    # ignore messages from the bot itself
    if user_id == bot_user_id:
        logger.info("Ignoring message from bot")
        return

     # ignore messages not in target channel
    if channel_id != TARGET_CHANNEL:
        logger.info(f"Ignoring message in wrong channel (expected {TARGET_CHANNEL}, got {channel_id})")
        return
    
    # Ignore edits and deletes (subtypes)
    if subtype is not None:
        logger.info(f"Ignoring message with subtype: {subtype}")
        return

    match = YUBIKEY_REGEX.search(text)
    if not match:
        logger.info("No Yubikey OTP found in message")
        return
    

    otp = match.group(0)
    validity = verify_otp(otp=otp)
    if validity:
        client.chat_postEphemeral(channel=channel_id, user=user_id, text="valid")
    else:
        client.chat_postEphemeral(channel=channel_id, user=user_id, text="invalid")

    

def verify_otp(otp: str) -> bool:
    nonce = secrets.token_hex(16)
    params = {
        "id": YUBICO_CLIENT_ID,
        "otp": otp,
        "nonce": nonce,
        "timestamp": "1",
        "sl": "secure",
    }

    # create HMAC-SHA1 signature using secret key

    message = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    key = base64.b64decode(YUBICO_SECRET_KEY)
    digest = hmac.new(key, message.encode("utf-8"), hashlib.sha1).digest()
    signature = base64.b64encode(digest).decode("utf-8")

    # add signature
    params["h"] = signature
    url = f"https://api.yubico.com/wsapi/2.0/verify?{urllib.parse.urlencode(params)}"

    try:
        res = requests.get(url, timeout=5)
        return "status=OK" in res.text
    except Exception as e:
        print(f"Yubico verification error: {e}")
        return False

def initalise_otp(slack_app):
    global app, bot_user_id
    app = slack_app
    bot_user_id = app.client.auth_test()["user_id"]

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

    logger.info(f"{program_name} initialised")