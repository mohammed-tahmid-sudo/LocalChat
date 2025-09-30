#####################################################################################################
import socket
import time
import json
import sqlite3
import threading

######################################################################################################


def initialize():
    conn = sqlite3.connect("/home/tahmid/LocalChat/backend/data/users.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            lastseen TEXT
            )
        """
    )
    conn.commit()
    conn.close()

    conn2 = sqlite3.connect("/home/tahmid/LocalChat/backend/data/holder.db")
    cursor2 = conn2.cursor()

    cursor2.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            sender_id TEXT,
            reciver_id TEXT
            message TEXT

        )

        """
    )
    conn2.commit()
    conn2.close()


######################################################################################################

def handle_client(conn, addr):

    db = sqlite3.connect("/home/tahmid/LocalChat/backend/data/users.db")
    cursor = db.cursor()

    print(f"Connected by {addr}")

######################################################################################################
    while True:
        try:
            data = conn.recv(2048)

            # json_data = json.loads(data)

            if not data:
                break

            msg = json.loads(data.decode())

            print(f"From {addr}: {msg}")

######################################################################################################

            if msg["type"] == "create_user":

                cursor.execute(
                    """
                    INSERT INTO users (name, lastseen) VALUES (?, ?)

                """,
                    (msg["name"], time.time()),
                )
                db.commit()

                data = {"type": "user_id", "id": cursor.lastrowid}

                conn.sendall(json.dumps(data).encode())

######################################################################################################

            elif msg["type"] == "ping":

                cursor.execute(
                    """
                    UPDATE users 
                    SET lastseen = ?
                    WHERE id = ?

                """,
                    (time.time(), msg["id"]),
                )
                db.commit()

######################################################################################################

            else:
                conn.sendall(b"ACK: " + data)

######################################################################################################

        except Exception as e:
            print(e)

    db.close
    print(f"Disconnected {addr}")


######################################################################################################

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 12345))
    server.listen()
    print("Server listening on 0.0.0.0:12345")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


######################################################################################################

if __name__ == "__main__":
    initialize()
    main()

######################################################################################################
