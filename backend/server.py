import socket

# Create a socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind to localhost on port 12345
server.bind(('127.0.0.1', 12345))

# Listen for connections
server.listen(1)
print("Waiting for a connection...")

while True: 
        conn, addr = server.accept()
        print(f"Connected by {addr}")

        # Receive data
        data = conn.recv(2048 * 2)
        print("Received:", data.decode())

        # Send response
        conn.send(b"Hello from server!")


        # Close connection
        # conn.close()

