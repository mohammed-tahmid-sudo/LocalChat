import socket

client = socket.socket()
client.connect(("127.0.0.1", 12345))

while True:
    msg = input("You: ")
    client.send(msg.encode())

    data = client.recv(1024)
    print("Other:", data.decode())

