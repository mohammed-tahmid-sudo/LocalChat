import socket
import json
import sqlite3
import threading
import time

HOST = "0.0.0.0"
PORT = 12345

CURRENT_TIME = int(time.time())

users = sqlite3.connect("/home/tahmid/LocalChat/backend/data/usernames.db")
ucur = users.cursor()

ucur.execute(
    """ CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT, last_seen STRING REAL)
"""
)

holder = sqlite3.connect("/home/tahmid/LocalChat/backend/data/holder.db")

hcur = holder.cursor()

hcur.execute(
    """
CREATE TABLE IF NOT EXISTS holder (sender_id TEXT, reciver_id TEXt, msg TEXT) 
    """
)


users.commit()
users.close()

holder.commit()
holder.commit()


def handle_client(conn, addr):
    database = sqlite3.connect(
        "/home/tahmid/LocalChat/backend/data/usernames.db",
        check_same_thread=False,  # allows usage in multiple threads if needed
    )
    db = database.cursor()

    try:
        while True:

            text = conn.recv(2**12)
            if not text:
                break
            try:
                text_json = json.loads(text)
                if "CREATE_USER" in text_json:
                    user_info = text_json["CREATE_USER"]
                    print(user_info)
                    db.execute(
                        """INSERT INTO users (username, last_seen) VALUES (?,?)""",
                        (user_info["NAME"], CURRENT_TIME),
                    )
                    database.commit()
                elif "SEND_MESSAGE" in text_json:
                    msg_info = text_json["SEND_MESSAGE"]
                    msg_id = msg_info["TO(ID)"]
                    print(msg_id)
                    db.execute("SELECT * FROM users WHERE id = ?", (msg_id,))
                    id = db.fetchone()
                    print(id)

                else:
                    print("debug INFO, got into the else statement")

            except Exception as e:
                print(e)
    except:
        print("SOME ERROR OCCURED")
    finally:
        conn.close()


def start_server():
    while True:  # restart server if it crashes
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # <-- add this
            server.bind((HOST, PORT))
            server.listen(1000)
            print(f"Listening on {HOST}:{PORT}")
            while True:
                conn, addr = server.accept()

                threading.Thread(target=handle_client, args=(conn, addr)).start()
        except Exception as e:
            print("Server crashed, restarting in 3 seconds:", e)
            time.sleep(3)


start_server()
