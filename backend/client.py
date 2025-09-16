# client.py
import socket, threading, sys

def recv_loop(sock):
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                print("\nDisconnected from server")
                break
            print("\n<peer>:", data.decode(errors="ignore"))
    except:
        pass
    finally:
        try: sock.close()
        except: pass
        sys.exit(0)

def main(host="127.0.0.1", port=12345):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    threading.Thread(target=recv_loop, args=(s,), daemon=True).start()
    # sender loop: can type many messages without waiting for reply
    try:
        while True:
            msg = input("\n<peer> ")
            if not msg:
                continue
            s.sendall(msg.encode())
    except KeyboardInterrupt:
        pass
    finally:
        s.close()

if __name__ == "__main__":
    main()

