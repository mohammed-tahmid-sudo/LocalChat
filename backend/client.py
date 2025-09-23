import socket
import threading

def receive(sock):
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data:
                break
            print("\n[Server]:", data)
        except:
            break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 5000))

    threading.Thread(target=receive, args=(sock,), daemon=True).start()

    while True:
        msg = input()
        if msg.lower() == "quit":
            break
        sock.sendall(msg.encode())

    sock.close()

if __name__ == "__main__":
    main()

