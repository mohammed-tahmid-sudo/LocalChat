#####################################################################################################
import socket
import time
import json
import sqlite3
import threading

#####################################################################################################

clients = {}  # keep track of connected clients


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
            reciver_id TEXT,
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

    holder_db = sqlite3.connect("/home/tahmid/LocalChat/backend/data/holder.db")
    holder_cursor = holder_db.cursor()

    print(f"Connected by {addr}")

    ######################################################################################################
    while True:
        try:
            data = conn.recv(2048)

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

                user_id = cursor.lastrowid
                clients[user_id] = conn  # store this client

                data = {"type": "user_id", "id": user_id}
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

                clients[msg["id"]] = conn

            ######################################################################################################

            elif msg["type"] == "message":
                sender_id = msg["sender"]
                reciver_id = msg["reciver"]
                message = msg["message"]

                cursor.execute(
                    """ 
                   SELECT lastseen FROM users WHERE id = ?
                """,
                    (reciver_id,),
                )
                reciver_lastseen = cursor.fetchone()

                if (
                    reciver_lastseen
                    and int(float(reciver_lastseen[0])) + 5 < time.time()
                ):

                    holder_cursor.execute(
                        """
                        INSERT INTO users (sender_id, reciver_id, message) VALUES (?, ?, ?)
                    """,
                        (sender_id, reciver_id, message),
                    )
                    holder_db.commit()
                else:
                    # forward directly if recipient is online
                    if reciver_id in clients:
                        clients[reciver_id].sendall(
                            json.dumps(
                                {
                                    "type": "message",
                                    "sender": sender_id,
                                    "message": message,
                                }
                            ).encode()
                        )
                    else:
                        # fallback: store if not connected
                        holder_cursor.execute(
                            """
                            INSERT INTO users (sender_id, reciver_id, message) VALUES (?, ?, ?)
                        """,
                            (sender_id, reciver_id, message),
                        )
                        holder_db.commit()

            ######################################################################################################

            else:
                conn.sendall(b"ACK: " + data)

        ######################################################################################################

        except Exception as e:
            print(e)
            break

    db.close()
    holder_db.close()

    # remove from clients dict on disconnect
    for uid, c in list(clients.items()):
        if c == conn:
            del clients[uid]
            break

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

#####################################################################################################
