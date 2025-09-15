import socket
import threading

# ----- Server part (listen for incoming messages) -----
def server(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", port))   # listen on all interfaces
    s.listen(1)
    print(f"[Server] Listening on port {port}...")

    while True:
        conn, addr = s.accept()
        data = conn.recv(1024).decode()
        if not data:
            break
        print(f"\n[{addr[0]}] {data}")
        conn.close()

# ----- Client part (send messages to target IP/port) -----
def client():
    while True:
        try:
            target = input("Enter target IP:Port (or 'quit'): ")
            if target.lower() == "quit":
                break
            ip, port = target.split(":")
            port = int(port)

            msg = input("Message: ")

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            s.send(msg.encode())
            s.close()
        except Exception as e:
            print("Error:", e)

# ----- Main -----
if __name__ == "__main__":
    my_port = int(input("Enter your listening port: "))

    # start server thread
    threading.Thread(target=server, args=(my_port,), daemon=True).start()

    # run client loop
    client()

