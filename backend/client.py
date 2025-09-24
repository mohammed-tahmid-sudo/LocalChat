import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

def client():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print("sending hello world") 
        s.sendall(b'Hello server!\n')
        print(s.recv(1024).decode())
        s.close()
    except Exception as e:
        print("Error:", e)

threads = []
for _ in range(1000):
    t = threading.Thread(target=client)
    t.start()
    threads.append(t)

for t in threads:
    t.join()

