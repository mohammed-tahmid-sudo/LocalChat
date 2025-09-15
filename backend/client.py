import socket

# Create a socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server
client.connect(('127.0.0.1', 12345))

# Send data
for _ in range(1, 1000): 
        client.send(b"Hello from client!\n")

# Receive response
data = client.recv(1024)
print("Received:", data.decode())

# Close connection
client.close()

