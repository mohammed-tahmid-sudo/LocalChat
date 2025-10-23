import asyncio
import websockets

async def process_task(data):
    # simulate long-running task
    await asyncio.sleep(2)
    return f"Processed: {data}"

async def handler(websocket):
    async for message in websocket:
        result = await process_task(message)
        await websocket.send(result)

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()  # run forever

asyncio.run(main())

