# server.py
import socket, threading

def handle_client(client, peers):
    try:
        while True:
            data = client.recv(4096)
            if not data:
                break
            # forward to all other clients immediately
            for p in peers.copy():
                if p is not client:
                    try:
                        p.sendall(data)
                    except:
                        try: p.close()
                        except: pass
                        if p in peers: peers.remove(p)
    finally:
        if client in peers: peers.remove(client)
        try: client.close()
        except: pass

def main(host="0.0.0.0", port=12345):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen()
    peers = []
    print("listening", host, port)
    while True:
        client, addr = srv.accept()
        peers.append(client)
        threading.Thread(target=handle_client, args=(client, peers), daemon=True).start()

if __name__ == "__main__":
    main()

