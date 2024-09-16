import asyncio
import json
import logging
from PyQt5.QtCore import pyqtSignal, QObject, QThread
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.signaling import TcpSocketSignaling
from aiortc.mediastreams import MediaStreamTrack

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

class WebRTCClient(QObject):
    frame_received = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()
        self.config = RTCConfiguration([RTCIceServer(urls=["stun:stun.l.google.com:19302"])])
        self.pc = RTCPeerConnection(configuration=self.config)
        self.signaling = TcpSocketSignaling("localhost", 4000)

    async def connect(self):
        await self.signaling.connect()

        @self.pc.on("track")
        async def on_track(track):
            logger.info("Track received")
            if track.kind == "video":
                while True:
                    frame = await track.recv()
                    logger.debug("Frame received")
                    self.frame_received.emit(frame.to_rgb().to_bytes())
        
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
            raise

class WebRTCThread(QThread):
    def __init__(self, webrtc_client):
        super().__init__()
        self.webrtc_client = webrtc_client
    
    def run(self):
        try:
            self.webrtc_client.run()
        except Exception as e:
            logger.error("Error in WebRTCThread: %s" % e)
            raise