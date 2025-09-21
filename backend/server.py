import json
import socket

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind(("0.0.0.0", 12345))
soc.listen(2)

conn1, addr1 = soc.accept()
conn2, addr2 = soc.accept()

while True:

    # Receive from client 1
    data1 = conn1.recv(2048)
    if data1:
        data1_json = json.loads(data1.decode())
        print("Received data from client 1:")
        print(data1_json)

    # Receive from client 2
    data2 = conn2.recv(2048)
    if data2:
        data2_json = json.loads(data2.decode())
        print("Received data from client 2:")
        print(data2_json)

