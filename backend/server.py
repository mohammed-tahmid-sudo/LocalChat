import socket
import threading

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode()
            print(f"From {addr}: {msg}")
            if msg == "PING":
                conn.sendall(b"PONG")
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
    main()

