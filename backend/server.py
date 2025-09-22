import socket
import json
import threading
import sqlite3

db = sqlite3.connect("/home/tahmid/LocalChat/backend/data/data.db")

if db:
    print("DataBase Created or It was ALready Created ")
c = db.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE
            )""")
c.execute("""CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                name TEXT
            )""")
c.execute("""CREATE TABLE IF NOT EXISTS room_members (
                room_id TEXT,
                user_id TEXT,
                PRIMARY KEY(room_id, user_id)
            )""")
c.execute("""CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                room_id TEXT,
                sender_id TEXT,
                content TEXT,
                type TEXT DEFAULT 'text',
                timestamp TEXT
            )""")
db.commit()


def handle_client(conn, name):
    while True:
        try:
            data = conn.recv(2048)
            if not data:
                break
            data_json = json.loads(data.decode())
            print(f"Received from {name}: {data_json}")
        except:
            break
    conn.close()


soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind(("0.0.0.0", 12345))
soc.listen(2)
print("Server listening...")

conn1, addr1 = soc.accept()
print("Client 1 connected:", addr1)
threading.Thread(target=handle_client, args=(conn1, "Client1"), daemon=True).start()

conn2, addr2 = soc.accept()
print("Client 2 connected:", addr2)
threading.Thread(target=handle_client, args=(conn2, "Client2"), daemon=True).start()

# Keep server running
while True:
    pass

