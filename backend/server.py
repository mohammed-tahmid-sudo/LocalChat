import socket, json, threading

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

