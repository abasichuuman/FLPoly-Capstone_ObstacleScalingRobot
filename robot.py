import asyncio
import json
import websockets
from aiortc import RTCPeerConnection, RTCSessionDescription

pc = None

async def run_robot():
    global pc
    while True:
        try:
            async with websockets.connect("ws://127.0.0.1:8765") as ws:
                print("Robot connected to Matchmaker. Waiting for laptop...")
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if "sdp" in data:
                        if pc:
                            await pc.close()
                        pc = RTCPeerConnection()

                        @pc.on("datachannel")
                        def on_datachannel(channel):
                            print("WebRTC LINK ACTIVE!")
                            @channel.on("message")
                            def on_message(message):
                                print(f"Laptop sent: {message}")
                                channel.send(f"Robot confirms: {message}")
                            @channel.on("close")
                            def on_close():
                                print("Browser disconnected.")

                        desc = RTCSessionDescription(sdp=data["sdp"]["sdp"], type=data["sdp"]["type"])
                        await pc.setRemoteDescription(desc)
                        if desc.type == "offer":
                            answer = await pc.createAnswer()
                            await pc.setLocalDescription(answer)
                            await ws.send(json.dumps({
                                "sdp": {
                                    "sdp": pc.localDescription.sdp,
                                    "type": pc.localDescription.type
                                }
                            }))
        except Exception as e:
            print(f"Error: {e} - retrying in 2s...")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(run_robot())
