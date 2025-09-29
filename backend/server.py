import socket
import json
import sqlite3
import threading


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

    conn = sqlite3.connect("/home/tahmid/LocalChat/backend/data/holder.db")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            sender_id TEXT, 
            reciver_id TEXT
            message TEXT
    
        )

        """
    )
    conn.commit()
    conn.close()


def handle_client(conn, addr):
        
    db = sqlite3.connect("/home/tahmid/LocalChat/backend/data/users.db")
    cursor = conn.cursor()
    db.commit()
    db.close()




    print(f"Connected by {addr}")
    while True:
        try:
            data = conn.recv(2048)

            # json_data = json.loads(data)

            if not data:
                break

            msg = json.loads(data.decode())

            print(f"From {addr}: {msg}")

            if "ping" in msg:
                cursor.execute("""
                    UPDATE users 
                    SET lastseen = ?,
                    WHERE id = ?

                """, (msg["ping"]["id"]))
            

            else:
                conn.sendall(b"ACK: " + data)

        except:
            break
    conn.close()
    print(f"Disconnected {addr}")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 12345))
    server.listen()
    print("Server listening on 0.0.0.0:12345")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    initialize()
    main()
