import socket
import sqlite3
import json
import threading
import secrets
import string

HOST = "127.0.0.1"
PORT = 12345

#### TESTING ####

def random_password(length=16):
    chars = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(chars) for _ in range(length))


def client():
    password1 = random_password()
    password2 = random_password()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    print("sending a dummy json")

    data = {"SEND_MESSAGE": {"NAME": random_password(5), "TO(ID)": "1"}}

    s.sendall(json.dumps(data).encode())
    # print(s.recv(1024).decode())

    s.close()


client()

#
# conn = sqlite3.connect("/home/tahmid/LocalChat/backend/data/usernames.db")
#
# cur = conn.cursor()
#
# cur.execute("SELECT * FROM users")
# print("\nAll users:")
# for row in cur.fetchall():
#     print(row)
