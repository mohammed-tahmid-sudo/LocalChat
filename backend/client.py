import asyncio

async def client(name):
    reader, writer = await asyncio.open_connection('127.0.0.1', 5000)

    async def send_messages():
        while True:
            msg = input(f"{name}: ")
            writer.write(msg.encode())
            await writer.drain()

    async def receive_messages():
        while True:
            data = await reader.read(1024)
            if not data:
                print("Connection closed")
                break
            print(f"Received: {data.decode()}")

    await asyncio.gather(send_messages(), receive_messages())

asyncio.run(client("Client1"))  # change to "Client2" for second client

