import hashlib
import socket
import platform
import os
from dotenv import load_dotenv


load_dotenv()

def host_fingerprint():

    parts = []

    parts.append(socket.gethostname())
    parts.append(platform.system())
    parts.append(platform.machine())

    mid = get_linux_machine_id()

    if os.getenv("DOCKER_RUN"):
        raw = "|".join(parts)
        return hashlib.sha256(raw.encode()).hexdigest()[:7] + "_dock"

    if mid:
        return mid[:8] + "_mid"

    else:
        raw = "|".join(parts)
        return hashlib.sha256(raw.encode()).hexdigest()[:12]


def get_linux_machine_id():
    possible_paths = [
        "/etc/machine-id",
        "/var/lib/dbus/machine-id"
    ]

    for path in possible_paths:
        try:
            with open(path, "r") as p:
                machine_id = p.read().strip()
                if machine_id:
                    return machine_id
        except FileNotFoundError:
            continue
        except PermissionError:
            continue

    return None