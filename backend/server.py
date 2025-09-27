import socket
import json
import sqlite3
import threading
import time

HOST = "0.0.0.0"
PORT = 12345

############################################
# In-memory dictionary to track online users
connected_users = {}  # user_id -> socket
lock = threading.Lock()  # for thread-safe DB writes
############################################


def init_databases():
    # ----- Users DB -----
    with sqlite3.connect("/home/tahmid/LocalChat/backend/data/usernames.db") as users:
        ucur = users.cursor()
        ucur.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT,
                   last_seen REAL
               )"""
        )
        users.commit()

    # ----- Offline messages DB -----
    with sqlite3.connect("/home/tahmid/LocalChat/backend/data/holder.db") as holder:
        hcur = holder.cursor()
        ############################################
        # Drop the old table to fix column issues
        hcur.execute("DROP TABLE IF EXISTS holder")  
        ############################################
        hcur.execute(
            """CREATE TABLE holder (
                   sender_id TEXT,
                   reciver_id TEXT,
                   text TEXT
               )"""
        )
        holder.commit()


def handle_client(conn, addr):
    db = sqlite3.connect("/home/tahmid/LocalChat/backend/data/usernames.db",
                         check_same_thread=False)
    cursor = db.cursor()
    ############################################
    user_id = None  # Track this user's ID
    ############################################

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            try:
                msg_json = json.loads(data)

                # ----- CREATE USER -----
                if "CREATE_USER" in msg_json:
                    user_info = msg_json["CREATE_USER"]
                    username = user_info["NAME"]
                    cursor.execute(
                        "INSERT INTO users (username, last_seen) VALUES (?, ?)",
                        (username, time.time())
                    )
                    db.commit()
                    ############################################
                    user_id = cursor.lastrowid
                    connected_users[user_id] = conn  # Track online user
                    ############################################

                    # Send any offline messages
                    with sqlite3.connect("/home/tahmid/LocalChat/backend/data/holder.db") as holder:
                        hcur = holder.cursor()
                        hcur.execute(
                            "SELECT sender_id, text FROM holder WHERE reciver_id=?",
                            (user_id,)
                        )
                        for sender_id, text in hcur.fetchall():
                            ############################################
                            conn.sendall(f"[Offline]{sender_id}: {text}".encode())
                            ############################################

                        # Delete delivered offline messages
                        hcur.execute("DELETE FROM holder WHERE reciver_id=?", (user_id,))
                        holder.commit()

                # ----- SEND MESSAGE -----
                elif "SEND_MESSAGE" in msg_json:
                    msg_info = msg_json["SEND_MESSAGE"]
                    reciver_id = msg_info["reciver_id"]
                    text = msg_info["text"]
                    sender_id = msg_info["sender_id"]

                    ############################################
                    # Online: send directly
                    if reciver_id in connected_users:
                        connected_users[reciver_id].sendall(f"{sender_id}: {text}".encode())
                    # Offline: store in holder DB
                    else:
                        with lock, sqlite3.connect("/home/tahmid/LocalChat/backend/data/holder.db") as holder:
                            hcur = holder.cursor()
                            hcur.execute(
                                "INSERT INTO holder (sender_id, reciver_id, text) VALUES (?, ?, ?)",
                                (sender_id, reciver_id, text)
                            )
                            holder.commit()
                    ############################################

                else:
                    print("Unknown command:", msg_json)

            except Exception as e:
                print("Error handling message:", e)

    finally:
        ############################################
        # Cleanup on disconnect
        if user_id and user_id in connected_users:
            del connected_users[user_id]
        ############################################
        conn.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1000)
    print(f"Server listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    ############################################
    init_databases()
    ############################################
    start_server()

