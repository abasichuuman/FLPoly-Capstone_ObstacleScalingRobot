import asyncio
import json
import websockets
import cv2
import numpy as np
import fractions
from picamera2 import Picamera2
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame

primaryCam = Picamera2(0)
rearCam = Picamera2(1)
clawCam = cv2.VideoCapture(16)

primaryCam.configure(primaryCam.create_preview_configuration(main={"size": (1280,720)}))
rearCam.configure(rearCam.create_preview_configuration(main={"size": (1280,720)}))
clawCam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
clawCam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

primaryCam.start()
rearCam.start()

active_camera = 1

class VideoTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self):
        super().__init__()
        self.counter = 0

    async def recv(self):
        global active_camera
        pts, time_base = await self.next_timestamp()

        if active_camera == 1:
            frame = primaryCam.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif active_camera == 2:
            frame = rearCam.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        elif active_camera == 0:
            ret, frame = clawCam.read()
            if not ret:
                frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

pc = None
video_track = None

async def run_robot():
    global pc
    while True:
        try:
            async with websockets.connect("ws://127.0.0.1:8765") as ws:
                print("Robot connected to Matchmaker. Waiting for laptop...")
                while True:
                        raw = await ws.recv()
                        print(f"Received: {raw[:50]}")
                        data = json.loads(raw)
                        if "sdp" in data:
                            if pc:
                                await pc.close()
                            pc = RTCPeerConnection()

                            video_track = VideoTrack()
                            pc.addTrack(video_track)

                            @pc.on("datachannel")
                            def on_datachannel(channel):
                                print("WebRTC LINK ACTIVE!")
                                @channel.on("message")
                                def on_message(message):
                                    global active_camera
                                    try:
                                        data = json.loads(message)
                                        if data.get("action") == "switch_camera":
                                            active_camera = data["camera"]
                                            print(f"Switched to camera {active_camera}")
                                        elif data.get("action") == "move":
                                            left = data.get("leftMotor", 0)
                                            right = data.get("rightMotor", 0)
                                            print(f"Move: left={left} right={right}")
                                    except:
                                        print(f"Received: {message}")

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
            import traceback
            traceback.print_exc()
            print(f"Error: {e} - retrying in 2s...")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(run_robot())
