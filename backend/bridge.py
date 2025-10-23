# bridge.py
import asyncio, websockets, socket, threading, json
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345

def tcp_reader(tcp_sock, ws):
    while True:
        data = tcp_sock.recv(2048)
        if not data:
            break
        asyncio.run_coroutine_threadsafe(ws.send(data), asyncio.get_event_loop())

async def handle_client(ws):
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.connect((SERVER_HOST, SERVER_PORT))

    threading.Thread(target=tcp_reader, args=(tcp_sock, ws), daemon=True).start()

    async for msg in ws:
        tcp_sock.sendall(msg.encode())

async def main():
    async with websockets.serve(handle_client, "0.0.0.0", 8080):
        await asyncio.Future()

asyncio.run(main())

