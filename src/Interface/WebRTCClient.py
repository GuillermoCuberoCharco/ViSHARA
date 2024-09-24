import asyncio
import json
import logging
import cv2
import numpy as np
from PyQt6.QtCore import pyqtSignal, QObject, QThread
from aiortc import RTCPeerConnection, VideoStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.signaling import TcpSocketSignaling
from aiortc.mediastreams import MediaStreamError
from av import VideoFrame

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("WebRTCClient")

class CustomTcpSocketSignaling(TcpSocketSignaling):
    async def receive(self):
        data = await self.reader.readline()
        if not data:
            logger.warning("No data received")
            raise ConnectionError("No data received")
        try:
            message = data.decode()
            logger.debug("Received message: %s" % message)
            parsed_message = json.loads(message)
            logger.info("Parsed message: %s" % parsed_message)
            return self.object_from_string(json.dumps(parsed_message))
        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON: %s" % e)
            raise
        except Exception as e:
            logger.error("Error in CustomTcpSocketSignaling: %s" % e)
            raise
    
    async def send(self, obj):
        mesaage = self.object_to_string(obj)
        print("Sending message: %s" % mesaage)
        self.writer.write(json.dumps(mesaage).encode() + b"\n")
        await self.writer.drain()

class OpenCvVideoStreamTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        ret, frame = self.cap.read()
        if not ret:
            raise ConnectionError("Error reading frame")
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return VideoFrame.from_ndarray(frame, format="bgr24")

class WebRTCClient(QObject):
    frame_received = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.config = RTCConfiguration([RTCIceServer(urls=["stun:stun.l.google.com:19302"])])
        self.pc = RTCPeerConnection(configuration=self.config)
        self.signaling = TcpSocketSignaling("localhost", 4000)

    async def connect(self):
        await self.signaling.connect()

        @self.pc.on("track")
        def on_track(self, track):
            logger.info("Track received")
            if track.kind == "video":
               asyncio.ensure_future(self.process_video(track))
    
    async def process_video(self, track):
        while True:
            try:
                frame = await track.recv()
                if frame:
                    img = frame.to_ndarray(format="bgr24")
                    self.frame_received.emit(img)
            except MediaStreamError as e:
                logger.error("Error receiving frame: %s" % e)
                break
        
        @self.pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.info("ICE connection state is %s" % self.pc.iceConnectionState)

        @self.pc.on("icegatheringstatechange")
        async def on_icegatheringstatechange():
            logger.info("ICE gathering state is %s" % self.pc.iceGatheringState)

    async def start(self):
        await self.connect()

        try:

            # Wait for offer from the web application
            offer = await self.signaling.receive()
            logger.info("Received offer: %s" % offer)
            await self.pc.setRemoteDescription(offer)

            # Create and send answer
            answer = await self.pc.createAnswer()
            await self.pc.setLocalDescription(answer)
            await self.signaling.send(self.pc.localDescription)

            logger.info("WebRTC connection established")
        except Exception as e:
            logger.error("Error in WebRTCClient: %s" % e)
            raise

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.start())
            loop.run_forever()
        except Exception as e:
            logger.error("Error in WebRTCClient: %s" % e)
        finally:
            loop.close()

class WebRTCThread(QThread):
    def __init__(self, webrtc_client):
        super().__init__()
        self.webrtc_client = webrtc_client
    
    def run(self):
        self.webrtc_client.run()
  
  