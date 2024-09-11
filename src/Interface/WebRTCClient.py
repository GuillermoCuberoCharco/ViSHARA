import asyncio
import json
from PyQt5.QtCore import pyqtSignal, QObject, QThread
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.signaling import TcpSocketSignaling

class WebRTCClient(QObject):
    frame_received = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()
        self.pc = RTCPeerConnection()
        self.signaling = TcpSocketSignaling("localhost", 4000)

    async def connect(self):
        await self.signaling.connect()

        @self.pc.on("track")
        async def on_track(track):
            if isinstance(track, VideoStreamTrack):
                while True:
                    frame = await track.recv()
                    self.frame_received.emit(frame.to_rgb().to_bytes())

    async def start(self):
        await self.connect()

        # Wating for the offer
        offer = await self.signaling.receive()
        await self.pc.setRemoteDescription(offer)

        # Create the answer
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        await self.signaling.send(self.pc.localDescription)

    def run(self):
        asyncio.run(self.start())

class WebRTCThread(QThread):
    def __init__(self, webrtc_client):
        super().__init__()
        self.webrtc_client = webrtc_client
    
    def run(self):
        self.webrtc_client.run()