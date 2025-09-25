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
    """ CREATE TABLE IF NOT EXISTS users ( id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE)
"""
)

database.commit()
database.close()


def handle_client(conn, addr):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            text = conn.recv(2**12)

            try:
                text_json = json.loads(text)
            except:
                print("unable to load the json file. Maybe because it's not a json")
    except:
        pass
    finally:
        conn.close()


def start_server():
    while True:  # restart server if it crashes
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind((HOST, PORT))
            server.listen(1000)
            print(f"Listening on {HOST}:{PORT}")
            while True:
                conn, addr = server.accept()
                # the main work goes here
                print(f"connected with {addr}")
                print("performing operations")
                # text = conn.recv(2**12)

                # try:
                #     text_json = json.loads(text)
                # except:
                #     print("unable to load the json file. Maybe because it's not a json")

                threading.Thread(target=handle_client, args=(conn, addr)).start()
        except Exception as e:
            print("Server crashed, restarting in 3 seconds:", e)
            time.sleep(3)


start_server()
