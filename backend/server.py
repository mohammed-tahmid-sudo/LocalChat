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

            # print(f"connected with {addr}")
            text = conn.recv(2**12)
            if not text:
                break
            try:
                text_json = json.loads(text)
                print(text_json) 
            except:
                print("unable to load the json file. Maybe because it's not a json")
    except:
        print("SOME ERROR OCCURED")
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
            

                threading.Thread(target=handle_client, args=(conn, addr)).start()
        except Exception as e:
            print("Server crashed, restarting in a seconds:", e)
            time.sleep(3)


start_server()
