import asyncio
import websockets
import socket
import threading

TCP_HOST = "127.0.0.1"
TCP_PORT = 12345
WS_PORT = 8080


# Handle data between one WebSocket client and one TCP connection
async def handle_ws(websocket):
    loop = asyncio.get_running_loop()
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.connect((TCP_HOST, TCP_PORT))
    tcp_sock.setblocking(False)

    async def tcp_to_ws():
        while True:
            try:
                data = await loop.sock_recv(tcp_sock, 4096)
                if not data:
                    break
                await websocket.send(data.decode())
            except:
                break

    async def ws_to_tcp():
        async for msg in websocket:
            await loop.sock_sendall(tcp_sock, msg.encode())

    # Run both directions concurrently
    await asyncio.gather(tcp_to_ws(), ws_to_tcp())

    tcp_sock.close()


async def main():
    async with websockets.serve(handle_ws, "0.0.0.0", WS_PORT):
        print(f"WebSocket bridge running on ws://0.0.0.0:{WS_PORT}")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())

