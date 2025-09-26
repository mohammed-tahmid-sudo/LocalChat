import socket
import json
import sqlite3
import threading
import time

HOST = "0.0.0.0"
PORT = 12345

database = sqlite3.connect("/home/tahmid/LocalChat/backend/data/usernames.db")
db = database.cursor()

db.execute(
    """ CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT, last_seen STRING REAL)
"""
)
database.commit()
database.close()


def handle_client(conn, addr):
    database = sqlite3.connect(
        "/home/tahmid/LocalChat/backend/data/usernames.db",
        check_same_thread=False,  # allows usage in multiple threads if needed
    )
    db = database.cursor()

    try:
        while True:
            # database = sqlite3.connect(
            #     "/home/tahmid/LocalChat/backend/data/usernames.db",
            #     check_same_thread=False,  # allows usage in multiple threads if needed
            # )
            # db = database.cursor()
            #
            # # print(f"connected with {addr}")
            text = conn.recv(2**12)
            if not text:
                break
            try:
                text_json = json.loads(text)
                user_info = text_json.get("Create_User")
                print(user_info)
                if user_info:
                    print("USER INFO. CHECK")
                    db.execute(
                        """INSERT INTO users (username) VALUES (?)""",
                        (user_info["NAME"],),
                    )
                    database.commit()

                else:
                    print("left this part for the next thing")

            except Exception as e:
                print("ERROR!!!! CODE:", e)
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
