# checks if a specific user id is a channel manager
import os
import logging
import datetime
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.getenv("bot_token"))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))

os.makedirs(os.path.join(project_root, "logs", "sticky_notes"), exist_ok=True)

logging.basicConfig(
    level=logging.INFO ,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=os.path.join(project_root, "logs", "check_manager", f"{datetime.datetime.now().strftime('%Y-%m-%d')}.log"),
    filemode="a"
)

def check(channel_id, user_id, client):
    logging.info(f"check in check_manager.py started: channel {channel_id}, user {user_id}")
    if not client or not channel_id or not user_id:
        logging.error(f"The correct parameters were not passed")
        return None
    response = client.admin_roles_listAssignments(role_ids=["Rl0A"], entity_ids=channel_id)

    while True:
        try:
            assignments = response.get("role_assignments", [])
            for assignment in assignments:
                if assignment.get("user_id") == user_id:
                    return True
            cursor = response["response_metadata"]["next_cursor"]
            if cursor != "":
                response = client.admin_roles_listAssignments(role_ids=["Rl0A"], entity_ids=channel_id, cursor=cursor)
                continue
            else:
                return False
        except Exception as e:  
            logging.error(f"Exception while getting assignments: {e}")


if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("app_token")).start()