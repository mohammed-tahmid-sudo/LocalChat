import socket

s = socket.socket()
s.connect(("127.0.0.1", 5000))

while True:
    msg = input("You: ")
    s.sendall(msg.encode())
    print("Friend:", s.recv(1024).decode())

