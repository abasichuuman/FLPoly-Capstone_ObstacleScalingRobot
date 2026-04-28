import asyncio
import json
import websockets

connected = set()

async def handler(websocket):
    print("New client connected to Matchmaker!")
    connected.add(websocket)
    try:
        async for message in websocket:
            for client in connected:
                if client != websocket:
                    await client.send(message)
    except websockets.exceptions.ConnectionClosedError:
        print("Client abruptly disconnected.")
    except websockets.exceptions.ConnectionClosedOK:
        print("Client disconnected politely.")
    finally:
        connected.discard(websocket)

async def main():
    print("Matchmaker started on 0.0.0.0:8765...")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
