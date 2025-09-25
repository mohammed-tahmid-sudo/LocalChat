import socket
import json
import threading
import secrets
import string

HOST = "127.0.0.1"
PORT = 12345

def random_password(length=16):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(chars) for _ in range(length))

def client():
    password1 = random_password()
    password2 = random_password()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print("sending a dummy json")
        data = {"User_ID": password1, "MSG_To": password2, "MSG":"hello world"}
        s.sendall(json.dumps(data).encode())
        print(s.recv(1024).decode())
        s.close()
    except Exception as e:
        print("Error:", e)

threads = []
for _ in range(10000):
    t = threading.Thread(target=client)
    t.start()
    threads.append(t)

for t in threads:
    t.join()

