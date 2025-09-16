import os
import sqlite3
import logging
import threading
import datetime
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))

os.makedirs(os.path.join(project_root, "logs", "sticky_notes"), exist_ok=True)
os.makedirs(os.path.join(project_root, "db"), exist_ok=True)

logging.basicConfig(
    level=logging.INFO ,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=os.path.join(project_root, "logs", "sticky_notes", f"{datetime.datetime.now().strftime('%Y-%m-%d')}.log"),
    filemode="a"
)

logging.info("Sticky notes started")
logging.getLogger("slack_bolt").setLevel(logging.ERROR)

app = App(token=os.getenv("bot_token"))

# get user id so it doesn't flood itself
bot_user_id = app.client.auth_test()["user_id"]

# prevent the bot breaking when there's lots of messages being spammed
channel_locks = {}
debounce_timers = {}

# better for multiple threads
def get_connection():
    return sqlite3.connect(os.path.join(project_root, "db", "sticky_notes.db"))

def get_lock(channel_id):
    if channel_id not in channel_locks:
        channel_locks[channel_id] = threading.Lock()
    return channel_locks[channel_id]

def schedule_sticky_refresh(channel_id, client):
    def refresh():
        with get_lock(channel_id=channel_id):
            last_ts = get_last_sticky(channel_id=channel_id)
            if not last_ts:
                return
            
            prev_text = get_last_text(channel_id=channel_id)
            if not prev_text: 
                logging.error(f"prev_text is None in refresh() with channel {channel_id}")
                return
            
        try:
            client.chat_delete(channel=channel_id, ts=last_ts)
            delete_sticky(channel_id=channel_id)
            result = client.chat_postMessage(
                channel=channel_id,
                text=f":pushpin: {prev_text}"
            )
            set_last_sticky(channel_id=channel_id, timestamp=result["ts"], text=prev_text)
        except Exception as e:
            logging.error(f"Sticky refresh failed in {channel_id} with ts {last_ts}: {e}")
    if channel_id in debounce_timers:
        debounce_timers[channel_id].cancel()

    timer = threading.Timer(0.5, refresh)
    debounce_timers[channel_id] = timer
    timer.start()

# create table
with get_connection() as conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS sticky_messages (
            channel_id TEXT PRIMARY KEY,
            message_timestamp TEXT,
            contents TEXT
    )
    """)


@app.command("/sticky-note")
def sticky_note(ack, respond, command, client):
    name = "/sticky-note"
    ack()

    channel_id = command["channel_id"]
    user_id = command["user_id"]
    args = command["text"].split(" ", 1) # action, rest

    if not args[0] or args[0].lower() not in ["create", "edit", "remove"]:
        respond(text="Usage: `/sticky-note [create|edit|remove] <text>` (text is not needed when removing)")
        logging.info(f"User {user_id} used {name} command incorrectly in channel {channel_id}")
        return


    action = args[0].lower()
    text = args[1] if len(args) > 1 else None

    if action in ["create", "edit"] and not text:
        respond(text="You need to provide a message to create/edit!", response_type="ephemeral")
        logging.info(f"User {user_id} used {name} didn't provide message for action {action} in channel {channel_id}")

    # CREATE
    if action == "create":
        logging.info(f"User {user_id} ran create action in {name} command in channel {channel_id}")
        last_ts = get_last_sticky(channel_id=channel_id) # icl ts pmo sm xD
        logging.debug(f"timestamp: {last_ts}")
        if last_ts:
            respond(text="You already have a stickied message! ")
            logging.info(f"User {user_id} couldn't create sticky note because of an existing one {channel_id}")
            
        else:
            try:
                result = client.chat_postMessage(
                    channel=channel_id,
                    text=f":pushpin: {text}"
                )
                set_last_sticky(channel_id=channel_id, timestamp=result["ts"], text=text)
                logging.info(f"User {user_id} created sticky note in channel {channel_id} with text {text}")
            except Exception as e:
                logging.error(f"Failed to create sticky, ran by user {user_id} in channel {channel_id} with text {text}: {e}")
                respond(text="Failed to create sticky :(", response_type="ephemeral")
                return
            


    # EDIT
    elif action == "edit":
        logging.info(f"User {user_id} ran edit action in {name} command in channel {channel_id}")
        last_ts = get_last_sticky(channel_id=channel_id)
        logging.debug(f"message timestamp: {last_ts}")
        if not last_ts:
            respond(text="No message to edit!", response_type="ephemeral")
            logging.info(f"No message to edit, ran by user {user_id} in {channel_id}")
            return

        client.chat_update(channel=channel_id, ts=last_ts, text=f":pushpin: {text}")
        logging.info(f"User {user_id} successfully edited sticky note in channel {channel_id} with text {text}")

    # REMOVE
    elif action == "remove":
        logging.info(f"User {user_id} ran remove action in {name} command in channel {channel_id}")
        last_ts = get_last_sticky(channel_id=channel_id)
        logging.debug(f"timestamp: {last_ts}")
        if not last_ts:
            respond(text="No message to remove!", response_type="ephemeral")
            logging.info(f"No message to delete, ran by user {user_id} in {channel_id}")
            return
        
        try:
            client.chat_delete(channel=channel_id, ts=last_ts)
            delete_sticky(channel_id=channel_id)
            logging.info(f"User {user_id} successfully deleted sticky note in channel {channel_id} with text {text}")
        except Exception as e:
            respond(text = f"Failed to delete sticky :(", response_type="ephemeral")
            logging.error(f"Failed to delete sticky with timestamp {last_ts}, ran by user {user_id} in {channel_id}")
            return


# actual pin function lol
@app.message()
def check_sticky(message, client):
    # prevent the bot from calling itself
    if message.get("user") == bot_user_id:
        return
    
    channel_id = message["channel"]

    if not get_last_sticky(channel_id=channel_id):
        return

    # debounce and lock
    schedule_sticky_refresh(channel_id=channel_id, client=client)


# get last sticky for channel
def get_last_sticky(channel_id):
    with get_connection() as conn:
        row = conn.execute("SELECT message_timestamp FROM sticky_messages WHERE channel_id = ?", (channel_id,)).fetchone()
        if row and row[0]:
            return row[0]
        else:
            logging.warning(f"get_last_sticky(channel_id={channel_id}) returned None, this should be fine, right????")
            return None

def get_last_text(channel_id):
    with get_connection() as conn:
        row = conn.execute("SELECT contents FROM sticky_messages WHERE channel_id = ?", (channel_id, )).fetchone()
        if row and row[0]:
            return row[0]
        else:
            logging.warning(f"get_last_text(channel_id={channel_id}) returned None, this should be fine, right????")
            return None

# set last sticky with sqlite
def set_last_sticky(channel_id, timestamp, text):
    with get_connection() as conn:
        conn.execute("""
        INSERT INTO sticky_messages (channel_id, message_timestamp, contents)
        VALUES (?, ?, ?)
        ON CONFLICT(channel_id) DO UPDATE SET message_timestamp=excluded.message_timestamp, contents=excluded.contents
    """, (channel_id, timestamp, text))

def delete_sticky(channel_id):
    with get_connection() as conn:
        conn.execute("""
        DELETE FROM sticky_messages WHERE channel_id = ?
    """, (channel_id,))
    



if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("app_token")).start()