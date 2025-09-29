import socket
import threading
import time
import json

IS_USER_FOUND = False


######################################################

def send_ping(sock, id):

    while True:
        try:
            data = {
                "type":"ping", 
                "id": id
            }
            sock.sendall(json.dumps(data).encode())
        except Exception as e:
            print(e)
        time.sleep(5)


######################################################

try:
    with open("/home/tahmid/LocalChat/backend/userdata.json", "r") as d:
        userdata = json.load(d)
        IS_USER_FOUND = True


except FileNotFoundError as e:

    print("welcome!!\n")
    print("first Enter your name:")
    username = input()
    print("you're all set. maybe just for now!")

    data = {"name": username}

    with open("/home/tahmid/LocalChat/backend/userdata.json", "w") as f:
        json.dump(data, f, indent=8)

######################################################


def if_datafound():
    if IS_USER_FOUND:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect(("127.0.0.1", 12345))

        t = threading.Thread(target=send_ping, args=(conn, userdata["name"]))
        t.daemon = True
        t.start()

        while True:
            try:
                msg = conn.recv(1024).decode()
                # if not msg:
                #     break
                print("Received:", msg)
            except Exception as e:
                print(e)



if __name__ == '__main__':
    if_datafound()





