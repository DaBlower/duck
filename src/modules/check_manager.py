# checks if a specific user id is a channel manager
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.getenv("bot_token"))

def check(channel_id, user_id, client):
    result = client.admin_roles_listAssignments(role_ids=["Rl0A"], entity_ids=channel_id)
    
    if user_id in result:
        return True
    else:
        return False

if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("app_token")).start()