import socket
import threading
import time

def send_ping(sock):
    while True:
        try:
            sock.sendall(b"PING")
        except:
            break
        time.sleep(5)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 12345))

    # Start ping thread
    threading.Thread(target=send_ping, args=(sock,), daemon=True).start()

    # Main loop for receiving & sending custom messages
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            print("Received:", data.decode())

            # Example: send something else (not just ping)
            user_input = input("Enter message: ")
            sock.sendall(user_input.encode())

        except KeyboardInterrupt:
            break
        except:
            break

    sock.close()

if __name__ == "__main__":
    main()

