#:#################################################################################################
import socket
import time
import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

# MAX_THREADS = 10  # maximum concurrent clients
#####################################################################################################


class Colors:
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    RESET = "\033[0m"


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

                print(
                    f"[{Colors.GREEN}DEBUG{Colors.RESET}] FOUND SOME PENDING MESSAGES ON THE DATABASE"
                )

                for pending in messages:
                    print(
                        f"[{Colors.GREEN}DEBUG{Colors.RESET}] SENDING{len(messages)} MESSAGE"
                    )

                    data = {
                        "type": "message",
                        "from": pending[0],
                        "message": pending[1],
                    }
                    clients[msg["id"]].sendall(json.dumps(data).encode())
                print(
                    f"[{Colors.GREEN}DEBUG{Colors.RESET}] Message Sending FInished Now deleting the holders from the database"
                )

                holder_cursor.execute(
                    "DELETE FROM users WHERE reciver_id = ?", (msg["id"],)
                )

                holder_db.commit()

                print(f"[{Colors.GREEN}DEBUG{Colors.RESET}] REMOVDE THE EXESS DATA ")

        ######################################################################################################

        elif msg["type"] == "message":
            sender_id = msg["sender"]
            reciver_id = msg["reciver"]
            message = msg["message"]

            print(
                f"[{Colors.GREEN}DEBUG{Colors.RESET}] Got a new message form ID:{sender_id} TO ID:{reciver_id} message: {message}"
            )

            if reciver_id in clients:

                holder_cursor.execute(
                    """
                                    SELECT sender_id, message FROM users WHERE reciver_id = ?
                    """,
                    (reciver_id,),
                )
                messages = holder_cursor.fetchall()

                data = {
                    "type": "message",
                    "from": sender_id,
                    "message": message,
                }

                clients[reciver_id].sendall(json.dumps(data).encode())

            else:
                holder_cursor.execute(
                    "INSERT INTO users (sender_id, reciver_id, message) VALUES (?, ?, ?)",
                    (sender_id, reciver_id, message),
                )
                holder_db.commit()

        elif msg["type"] == "contact":

            cursor.execute("SELECT name, id FROM users")
            usernames = cursor.fetchall()
            data = {"type": "usernames", "usernames": []}

            data["usernames"] = [name for name in usernames]

            print(f"[{Colors.GREEN}INFO{Colors.RESET}] {usernames}")

            conn.sendall(json.dumps(data).encode())

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

    print(f"[{Colors.RED}RUNNING{Colors.RESET}] Server listening on 0.0.0.0:12345")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


# def main():
#     server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     server.bind(("0.0.0.0", 12345))
#     server.listen()
#
#     print(f"[{Colors.RED}RUNNING{Colors.RESET}] Server listening on 0.0.0.0:12345")
#
#     with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
#         while True:
#             conn, addr = server.accept()
#             executor.submit(handle_client, conn, addr)


######################################################################################################

if __name__ == "__main__":
    initialize()
    main()

#####################################################################################################
