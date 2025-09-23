import socket
import threading

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    while True:
        try:
            msg = conn.recv(1024).decode()
            if not msg:
                break
            print(f"[{addr}] {msg}")
            broadcast(msg, conn)
        except:
            break
    conn.close()

def broadcast(message, sender_conn):
    for c in clients:
        if c != sender_conn:
            try:
                c.send(message.encode())
            except:
                pass

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 12345))
server.listen()

clients = []
print("[SERVER STARTED] Waiting for connections...")

while True:
    conn, addr = server.accept()
    clients.append(conn)
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()

