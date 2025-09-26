import socket
import json
import threading
import secrets
import string

HOST = "127.0.0.1"
PORT = 12345


def random_password(length=16):
    chars = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(chars) for _ in range(length))


def client():
    password1 = random_password()
    password2 = random_password()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    print("sending a dummy json")

    data = {"Create_User": {"NAME": "BAKA/Dummy"}}


    s.sendall(json.dumps(data).encode())
    # print(s.recv(1024).decode())

    s.close()

for x in range(0, 100):
    client()

