import os, sqlite3, logging, datetime, re
from slack_sdk.errors import SlackApiError

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))

# initialise app variables for mains script to set
app = None
bot_user_id = None # get user id so it doesn't flood itself

logger = logging.getLogger("private_join")

# better for multiple threads-returns connection for adding and requesting
def get_connection():
    db_dir = os.path.join(project_root, "db")
    os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(os.path.join(db_dir, "private_adder.db"))

def new_joiner(ack, respond, command, client):
    """
    /new_joiner <channel_id> <alias>
    """
    ack()

    name = "/new_joiner"

    user_id = command["user_id"]
    args = command["text"].split(" ", 1) # channel, alias

    channel = args[0].strip().upper()
    alias = args[1].strip()
     
    if len(args) != 2:
        respond(
            text="Usage: `/new_joiner <channel_id> <alias>`",
            response_type="ephemeral"
        )
        return
    
    channel_regex = re.compile(r"(?:<#[C][A-Z0-9]{8,}>|[C][A-Z0-9]{8,})") # aghhhh i _dislike_ regex

    if not channel_regex.fullmatch(channel):
        respond(
            text="Invalid channel id format, either <#12345678> or 12345678",
            response_type="ephemeral"
        )
        return

    if check_alias(alias=alias):
        respond(
            text=f"This alias already exists! If you are a channel manager of <#{channel}>, you can delete it with `/delete_joiner {channel}`", # get channel here
            response_type="ephemeral"
        )

    if check_channel(channel=channel):
        respond(
            text=f"This channel already has a joiner! If you are a channel manager of <#{channel}>, you can delete it with `/delete_joiner {channel}`", # get channel here
            response_type="ephemeral"
        )

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO channel_registrations (alias, channel_id, creator_user_id)
                VALUES (?, ?, ?)
                """,
            (
                alias, channel, user_id
            )
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to register channel alias: {e}")
        respond(
            text="Something went wrong when registering this alias :(",
            response_type="ephemeral"
        )
        return
    respond(
        text=f"Alias *{alias}* now points to <#{channel}!",
        response_type="ephemeral"
    )



def join(ack, respond, command, client):
    """
    /join <alias>
    """
    ack()

    requester_id = command.get("user_id")
    alias = command.get("text", "").strip().lower()

    if not alias:
        respond(
            text="Usage: `/join <alias>`",
            response_type="ephemeral"
        )
        return
    
    with get_connection() as conn:
        row = conn.execute("""
            SELECT channel_id, creator_user_id
            FROM channel_registrations
            WHERE alias = ?
        """,
        (alias, )).fetchone

    if not row:
        respond(
            text=f"I can't find any private channels with alias `{alias}`.",
            response_type="ephemeral"
        )
    
    channel_id, creator_user_id = row

    # open a dm with the creator
    try:
        dm = client.conversations_open(users=creator_user_id)
        dm_channel = dm["channel"]["id"]
    except SlackApiError as e:
        logger.error("Failed to open DM with channel creator")
        respond(
            text="I couldn't contact the owner of the channel you are requesting to join (not your fault!), sorry :(",
            response_type="ephemeral"
        )
        return
    
    try:
        client.chat_postMessage(
            channel=dm_channel,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "requester is requesting access"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Approve",
                                "emoji": True
                            },
                            "style": "primary",
                            "value": f"accept|{channel_id}|{requester_id}|{alias}",
                            "action_id": "join_request_action"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Reject",
                                "emoji": True
                            },
                            "value": f"reject|{channel_id}|{requester_id}|{alias}",
                            "action_id": "join_request_action"
                        }
                    ]
                }
            ]
        )
    except SlackApiError:
        logger.error("Failed to send join request to the owner")
        respond(
            text="I couldn't send your request to the creator, sorry ): (not your fault!)",
            response_type="ephemeral"
        )
        return
    respond(
        text=f"Your request to join *{alias}* has been sent to the creator!",
        response_type="ephemeral"
    )

def join_request_action(ack, body, client, respond=None):
    ack()

    action = body["actions"][0]
    value = action.get("value", "")
    user_who_clicked = body["user"]["id"]

    try:
        decision, channel_id, requester_id, alias = value.split("|", 3)
    except ValueError:
        logger.error(f"Invalid join_request_action value: {value}")
        return
    
    with get_connection() as conn:
        row = conn.execute(
            """"
            SELECT creator_user_id
            FROM channel_registrations
            WHERE alias = ?
            """,
            (alias, )
        ).fetchone()

    if not row:
        # the alias doesn't exist anymore, so just silently stop
        return
    
    creator_user_id = row[0]
    if user_who_clicked != creator_user_id:
        client.chat_postEphemeral(
            channel=body["channel"]["id"],
            user=user_who_clicked,
            text="You are not the approver for this channel."
        )
        return
    
    

def check_alias(alias):
    with get_connection() as conn:
        existing = conn.execute("SELECT 1 FROM channel_registrations WHERE alias = ? LIMIT 1", (alias,)).fetchone()
        return existing is not None

def check_channel(channel):
    with get_connection() as conn:
        existing = conn.execute("SELECT 1 FROM channel_registrations WHERE channel_user_id = ? LIMIT 1", (channel,)).fetchone()
        return existing is not None
    
# get last sticky for channel
def get_last_sticky(channel_id):
    with get_connection() as conn:
        row = conn.execute("SELECT message_timestamp FROM sticky_messages WHERE channel_id = ?", (channel_id,)).fetchone()
        if row and row[0]:
            return row[0]
        else:
            logger.debug(f"get_last_sticky(channel_id={channel_id}) returned None, this should be fine, right????")
            return None

def delete_sticky(channel_id):
    with get_connection() as conn:
        conn.execute("""
        DELETE FROM sticky_messages WHERE channel_id = ?
    """, (channel_id,))
    

def initialise_sticky_command(slack_app):
    actual_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    global app, bot_user_id

    app = slack_app
    bot_user_id = app.client.auth_test()["user_id"]

    log_dir = os.path.join(actual_root, "logs", "sticky_notes")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(os.path.join(actual_root, "src", "commands", "db"), exist_ok=True)

    # create specific logger for this script
    logger = logging.getLogger("sticky_notes")
    logger.setLevel(logging.INFO)

    # remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # create file handler
    log_file = os.path.join(actual_root, "logs", "sticky_notes", f"{datetime.datetime.now().strftime('%Y-%m-%d')}.log")
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logging.INFO)

    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.info("Sticky notes initialised")

    logging.getLogger("slack_bolt").setLevel(logging.ERROR)

    # register command and message handlers (because app is None originally)
    app.command("/new-joiner")(new_joiner)
    app.command("/join")(join)

    # action for acceptance action
    app.action("join_request")(join_request_action)

    # create database table so messages stay persistent
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS channel_registrations (
            alias TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL,
            creator_user_id TEXT NOT NULL
        )
        """)
        """
        alias for the channel that a person uses to join (eg /join cow, instead of the channel id or name)"""