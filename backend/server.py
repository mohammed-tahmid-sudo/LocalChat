import asyncio
import threading

async def receive_messages(reader):
    while True:
        data = await reader.read(1024)
        if not data:
            print("Connection closed")
            break
        print(f"\nReceived: {data.decode()}")

def send_messages(writer, name):
    while True:
        msg = input(f"{name}: ")
        writer.write(msg.encode())
        asyncio.run_coroutine_threadsafe(writer.drain(), asyncio.get_event_loop())

async def main(name):
    reader, writer = await asyncio.open_connection('127.0.0.1', 5000)
    threading.Thread(target=send_messages, args=(writer, name), daemon=True).start()
    await receive_messages(reader)

asyncio.run(main("Client1"))

