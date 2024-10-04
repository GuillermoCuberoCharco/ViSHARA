import asyncio
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QThread, pyqtSignal, Qt
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, MediaStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaPlayer, MediaRecorder
import socketio
import av
import json
import cv2

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        frame = await self.track.recv()
        return frame

class WebRTCThread(QThread):
    connection_status = pyqtSignal(str)
    frame_received = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.pc = None
        self.running = True
        self.sio = None

    @staticmethod
    def parse_candidate(candidate_dic):
        parts = candidate_dic.split()
        return{
            'foundation': parts[0].split(':')[1],
            'component': int(parts[1]),
            'protocol': parts[2],
            'priority': int(parts[3]),
            'ip': parts[4],
            'port': int(parts[5]),
            'type': parts[7]
        }

    async def create_connection(self):
        if self.sio and self.sio.connected:
            await self.sio.disconnect()

        self.sio = socketio.AsyncClient(logger=True, engineio_logger=True)

        config = RTCConfiguration( 
            iceServers=[
                #RTCIceServer(urls=["stun:stun.l.google.com:19302"])
            ]
        )
        
        self.pc = RTCPeerConnection(configuration=config)
        logger.debug("RTCPeerConnection created")

        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.debug(f"Connection state changed to {self.pc.connectionState}")
            self.connection_status.emit(f"Connection state: {self.pc.connectionState}")
            if self.pc.connectionState == "failed":
                logger.error("Connection failed. Attempting to reconnect...")
                await self.recreate_connection()
        
        @self.pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.debug(f"ICE connection state changed to {self.pc.iceConnectionState}")
            self.connection_status.emit(f"ICE connection state: {self.pc.iceConnectionState}")

        @self.pc.on("track")
        def on_track(track):
            logger.debug(f"Track received: {track.kind}")
            if track.kind == "video":
                logger.debug("Video track received")
                video_track = VideoStreamTrack(track)
                @video_track.on("frame")
                def on_frame(frame):
                    logger.debug("Frame received")
                    img = frame.to_ndarray(format="bgr24")
                    self.frame_received.emit(img)

        try:
            await self.sio.connect('http://localhost:8081', namespaces=['/webrtc'])
            logger.debug("Connected to WebRTC server")
            await self.sio.emit('register', 'python', namespace='/webrtc')
            logger.debug("Registered with server as 'python' client")
        except Exception as e:
            logger.error(f"Failed to connect to server: {str(e)}")
            self.connection_status.emit(f"Connection failed: {str(e)}")
            return

        @self.sio.on('offer', namespace='/webrtc')
        async def on_offer(offer):
            logger.debug("Received offer")
            try:
                await self.pc.setRemoteDescription(RTCSessionDescription(sdp=offer['sdp'], type=offer['type']))
                logger.debug("Remote description set")

                answer = await self.pc.createAnswer()
                logger.debug("Answer created")
                await self.pc.setLocalDescription(answer)
                logger.debug("Local description set")
                await self.sio.emit('answer', {'sdp': answer.sdp, 'type': answer.type}, namespace='/webrtc')
                logger.debug("Answer sent")
            except Exception as e:
                logger.error(f"Error handling offer: {e}")

        @self.sio.on('ice-candidate', namespace='/webrtc')
        async def on_ice_candidate(candidate):
            logger.debug(f"Received ICE candidate: {candidate}")
            if candidate and 'candidate' in candidate:
                try:
                    candidate_str = candidate['candidate']
                    parsed_candidate = self.parse_candidate(candidate_str)
                    
                    candidate_obj = RTCIceCandidate(
                        component=parsed_candidate['component'],
                        foundation=parsed_candidate['foundation'],
                        ip=parsed_candidate['ip'],
                        port=parsed_candidate['port'],
                        priority=parsed_candidate['priority'],
                        protocol=parsed_candidate['protocol'],
                        type=parsed_candidate['type'],
                        sdpMid=candidate.get('sdpMid'),
                        sdpMLineIndex=candidate.get('sdpMLineIndex')
                    )
                    await self.pc.addIceCandidate(candidate_obj)
                    logger.debug("ICE candidate added successfully")
                except Exception as e:
                    logger.error(f"Error adding ICE candidate: {e}")
            #else:
                #logger.warning("Received invalid ICE candidate")

        @self.pc.on("icecandidate")
        def on_icecandidate(event):
            if event.candidate:
                candidate_data = {
                    'candidate': event.candidate.candidate,
                    'sdpMid': event.candidate.sdpMid,
                    'sdpMLineIndex': event.candidate.sdpMLineIndex,
                }
                logger.debug(f"Sending ICE candidate: {candidate_data}")
                asyncio.create_task(self.sio.emit('ice-candidate', candidate_data, namespace='/webrtc'))

    async def recreate_connection(self):
        logger.info("Recreating connection")
        if self.pc:
            await self.pc.close()
        if self.sio and self.sio.connected:
            await self.sio.disconnect()
        await asyncio.sleep(5)
        await self.create_connection()
    
    async def run_async(self):
         while self.running:
            try:
                await self.create_connection()
                while self.running and self.sio.connected:
                    await asyncio.sleep(1)
                    logger.debug("Current connection state: " + self.pc.connectionState)
            except Exception as e:
                logger.error(f"Error in WebRTCThread: {e}")
            finally:
                if self.pc:
                    await self.pc.close()
                if self.sio and self.sio.connected:
                    await self.sio.disconnect()

            if self.running:
                logger.info("Attempting to reconnect in 5 seconds...")
                await asyncio.sleep(5)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_async())

    async def stop(self):
        self.running = False
        if self.sio.connected:
            await self.sio.disconnect()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 WebRTC Test")
        self.setGeometry(100, 100, 640, 480)
        
        layout = QVBoxLayout()
        
        self.video_label = QLabel()
        layout.addWidget(self.video_label)
        
        self.status_label = QLabel("Status: Initializing...")
        layout.addWidget(self.status_label)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        self.webrtc_thread = WebRTCThread()
        self.webrtc_thread.connection_status.connect(self.update_status)
        self.webrtc_thread.frame_received.connect(self.display_frame)
        self.webrtc_thread.start()
        
        logger.debug("MainWindow initialized")

    def display_frame(self, img):
        logger.debug("Displaying frame")
        height, width, channel = img.shape
        bytes_per_line = 3 * width
        q_img = QImage(img.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio))

    def update_status(self, status):
        self.status_label.setText(f"Status: {status}")
        logger.debug(f"Status updated: {status}")

    def closeEvent(self, event):
        asyncio.run(self.webrtc_thread.stop())
        self.webrtc_thread.wait()
        super().closeEvent(event)

if __name__ == "__main__":
    logger.info("Starting application")
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()