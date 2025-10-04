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
        # try:
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

            holder_cursor.execute(
                """
                        SELECT sender_id, message FROM users WHERE reciver_id = ?
                    """,
                (msg["id"],),
            )
            messages = holder_cursor.fetchall()

            if messages:

                print("[DEBUG] FOUND SOME PENDING MESSAGES ON THE DATABASE")

                for msg in messages:
                    print(f"[DEBUG] SENDING{len(messages)} MESSAGE")

                    data = {
                        "type": "message",
                        "from": msg[0],
                        "message": msg[1],
                    }
                    clients[msg["id"]].sendall(json.dumps(data).encode())

        ######################################################################################################

        elif msg["type"] == "message":
            sender_id = msg["sender"]
            reciver_id = msg["reciver"]
            message = msg["message"]

            if reciver_id in clients:

                holder_cursor.execute(
                    """
                                    SELECT sender_id, message FROM users WHERE reciver_id = ?
                    """,
                    (reciver_id,),
                )
                messages = holder_cursor.fetchall()

                if messages:

                    print("[DEBUG] FOUND SOME PENDING MESSAGES ON THE DATABASE")
                    messages.append((sender_id, message))

                    for msg in messages:
                        print(f"[DEBUG] SENDING{len(message)} MESSAGE")

                        data = {
                            "type": "message",
                            "from": msg[0],
                            "message": msg[1],
                        }
                        clients[reciver_id].sendall(json.dumps(data).encode())

                else:
                    print("[DEBUG] IF THERE IS ANY ERROR THEN YOU'RE FUCKED")

                    data = {
                        "type": "message",
                        "from": sender_id,
                        "message": message,
                    }

                    clients[reciver_id].sendall(json.dumps(data).encode())

            # if reciver_lastseen < time.time() - 5:

        else:
            conn.sendall(b"ACK: " + data)

    ######################################################################################################

    # except Exception as e:
    #     print(e)
    #     break

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
