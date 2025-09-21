import socket
import json

# connect to server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.0", 12345))  # replace with server IP

while True:
    # example data to send
    data = {
        "name": input("Enter name: "),
        "age": int(input("Enter age: "))
    }

    # convert dict to JSON string and encode to bytes
    client.sendall(json.dumps(data).encode())
    print("Data sent to server.")

