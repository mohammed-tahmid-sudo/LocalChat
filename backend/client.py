import socket
import threading

def receive(sock):
    while True:
        try:
            msg = sock.recv(1024).decode()
            if not msg:
                break
            print("Friend:", msg)
        except:
            break

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 12345))

threading.Thread(target=receive, args=(sock,), daemon=True).start()

while True:
    msg = input("You: ")
    sock.send(msg.encode())

