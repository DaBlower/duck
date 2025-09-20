# checks if a specific user id is a channel manager
import os
import logging
import datetime
from slack_sdk import WebClient

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))

def get_client():
    user_token = os.getenv("user_token")
    if not user_token:
        logging.error("no user token found in env :(")
        return None
    return WebClient(token=user_token)

def check(channel_id, user_id):
    logging.info(f"check in check_manager.py started: channel {channel_id}, user {user_id}")
    if not channel_id or not user_id:
        logging.error(f"The correct parameters were not passed")
        return None
    
    client = get_client()
    if not client:
        logging.error("could not create client")
        return False

    try:
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
    except Exception as e:
        logging.error(f"Exception while in check(): {e}")
        return False

def initialise_check_manager():
    os.makedirs(os.path.abspath(os.path.join(project_root, "..", "..", "logs", "check_manager")), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO ,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename=os.path.abspath(os.path.join(project_root, "..", "..", "logs", "check_manager", f"{datetime.datetime.now().strftime('%Y-%m-%d')}.log")),
        filemode="a"
    )