##############################################################################################################
import socket
import threading
import time
import json
import os

##############################################################################################################


def send_ping(sock, user_id):
    while True:
        try:
            data = {"type": "ping", "id": user_id}
            sock.sendall(json.dumps(data).encode())
        except Exception as e:
            print("error at line 21:", e)
            break
        time.sleep(5)


def message(conn, userdata):
    def recv_thread():
        while True:
            try:
                msg = conn.recv(2048).decode()
                if not msg:
                    break
                print("Received:", msg)
            except:
                break

    # threading.Thread(target=recv_thread, daemon=True).start()


    data = {"type": "contact"}
    conn.sendall(json.dumps(data).encode())
    message = conn.recv_thread(2048).decode()

    for msg in message:
        print(msg)

    print("Select a number which corrosponds to the user")
    id = input("-> ")

    if id

    threading.Thread(target=recv_thread, daemon=True).start()

    # to = None
    # while True:
    #     if to is None:
    #         print("this is a list of users and type the number shoing that message that person")
    #
    #         to = input("type the number:  ")
    #
    #     print("TYPE @lu to list all the users")
    #     sent = input("TYPE: ")
    #
    #
    #     if sent.lower() == "@lu":
    #         data = {"type": "contact"}
    #     elif to is not None:
    #         to = int(input("TO WHO?: "))
    #         data = {"type": "message", "sender": userdata["id"], "reciver": to, "message": sent}
    #     try:
    #         conn.sendall(json.dumps(data).encode())
    #     except Exception as e:
    #         print("Error sending message:", e)
    #         break


##############################################################################################################


def if_user_found(conn, userdata):
    t = threading.Thread(target=send_ping, args=(conn, userdata["id"]))
    t.daemon = True
    t.start()


##############################################################################################################
def if_user_notfound(conn, username):
    data = {"type": "create_user", "name": username}
    conn.sendall(json.dumps(data).encode())
    print(f"{data} sent")

    recived_data = conn.recv(2**10).decode()

    try:
        parsed = json.loads(recived_data)
        with open("userdata.json", "w") as f:
            json.dump(parsed, f, indent=4)
        print("data Created")
        return parsed
    except json.JSONDecodeError:
        print("Received non-JSON data:", recived_data)
        return None


##############################################################################################################

if __name__ == "__main__":
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect(("127.0.0.1", 12345))

    userdata = None
    if os.path.exists("userdata.json"):
        with open("userdata.json", "r") as d:
            userdata = json.load(d)
        if userdata:
            if_user_found(conn, userdata)
            message(conn, userdata)

    # elif not os.path.exists("/userdata.json"):
    else:
        print("enter your name: ")
        inp = input()
        userdata = if_user_notfound(conn, inp)
        if userdata:
            if_user_found(conn, userdata)
            message(conn, userdata)

##############################################################################################################
