import socket
import json
import threading

HOST = "127.0.0.1"  # server IP
PORT = 12345

username = input("Enter your username: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# Send CREATE_USER to server
client.sendall(json.dumps({"CREATE_USER": {"NAME": username}}).encode())

# Thread to receive messages
def receive_messages():
    while True:
        try:
            data = client.recv(4096)
            if not data:
                break
            print(data.decode())
        except:
            break

threading.Thread(target=receive_messages, daemon=True).start()

# Main loop to send messages
while True:
    try:
        msg = input()
        if msg.lower() == "/quit":
            break

        # Example: send to a specific user by ID
        receiver_id = input("Send to user ID: ")

        send_data = {
            "SEND_MESSAGE": {
                "sender_id": username,  # you can use DB ID if needed
                "reciver_id": int(receiver_id),
                "text": msg
            }
        }
        client.sendall(json.dumps(send_data).encode())

    except KeyboardInterrupt:
        break

client.close()

