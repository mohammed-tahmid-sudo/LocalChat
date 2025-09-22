import socket
import json
from datetime import datetime, timezone

ts = datetime.now(timezone.utc).isoformat(timespec='seconds')

# connect to server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.0", 12345))  # replace with server IP

while True:
    # example data to send
    data = {
        # "action": input("ENTER YOUR MESSAGE: "),
        "id": "123456789",
        "sender": input("NAME: "),
        "content": input("content: "),
        "timestamp": ts
    }

    # convert dict to JSON string and encode to bytes
    client.sendall(json.dumps(data).encode())
    print("Data sent to server.")
