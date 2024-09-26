import sys
import asyncio
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
import numpy as np
import logging
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack, RTCIceCandidate
from av import VideoFrame
import fractions

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FakeVideoStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self):
        super().__init__()
        self.counter = 0

    async def recv(self):
        self.counter += 1
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        text = f"WebRTC Frame {self.counter}"
        img = self.put_text(img, text, (50, 50))
        frame = VideoFrame.from_ndarray(img, format="rgb24")
        frame.pts = self.counter
        frame.time_base = fractions.Fraction(1, 30)
        return frame

    def put_text(self, img, text, position):
        from PIL import Image, ImageDraw, ImageFont
        pil_img = Image.fromarray(img)
        draw = ImageDraw.Draw(pil_img)
        font = ImageFont.load_default()
        draw.text(position, text, font=font, fill=(255, 255, 255))
        return np.array(pil_img)

class WebRTCThread(QThread):
    connection_status = pyqtSignal(str)
    frame_received = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.pc = None
        self.running = True

    async def start_connection(self):
        self.pc = RTCPeerConnection()
        logger.debug("RTCPeerConnection created")
        self.connection_status.emit("RTCPeerConnection created")

        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.debug(f"Connection state is {self.pc.connectionState}")
            self.connection_status.emit(f"Connection state: {self.pc.connectionState}")

        @self.pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.debug(f"ICE connection state is {self.pc.iceConnectionState}")
            self.connection_status.emit(f"ICE connection state: {self.pc.iceConnectionState}")

        fake_track = FakeVideoStreamTrack()
        self.pc.addTrack(fake_track)
        logger.debug("Fake video track added")
        self.connection_status.emit("Fake video track added")

        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        logger.debug("Local description set")
        self.connection_status.emit("Local description set")

        # Create a more realistic answer
        answer_sdp = offer.sdp.replace("a=setup:actpass", "a=setup:active")
        fake_answer = RTCSessionDescription(sdp=answer_sdp, type="answer")
        await self.pc.setRemoteDescription(fake_answer)
        logger.debug("Fake remote description set")
        self.connection_status.emit("Fake remote description set")

        # Simulate ICE candidate exchange
        fake_candidate = RTCIceCandidate(
            component=1,
            foundation="1",
            ip="192.168.1.1",
            port=1234,
            priority=1,
            protocol="udp",
            type="host",
            sdpMid="0",
            sdpMLineIndex=0
        )
        await self.pc.addIceCandidate(fake_candidate)
        logger.debug("Fake ICE candidate added")
        self.connection_status.emit("Fake ICE candidate added")

        # Simulate successful connection after a short delay
        await asyncio.sleep(2)
        logger.debug("Simulating successful connection")
        self.connection_status.emit("Connected (simulated)")

        @self.pc.on("track")
        def on_track(track):
            logger.debug(f"Track received: {track.kind}")
            if track.kind == "video":
                @track.on("frame")
                def on_frame(frame):
                    img = frame.to_ndarray(format="rgb24")
                    self.frame_received.emit(img)

    async def run_async(self):
        try:
            await self.start_connection()
            frame_count = 0
            while self.running:
                await asyncio.sleep(1/30)  # Simulate 30 FPS
                frame = await FakeVideoStreamTrack().recv()
                img = frame.to_ndarray(format="rgb24")
                self.frame_received.emit(img)
                frame_count += 1
                if frame_count % 30 == 0:  # Log every second
                    logger.debug(f"Generated frame {frame_count}")
        except Exception as e:
            logger.error(f"Error in WebRTCThread: {e}")
            self.connection_status.emit(f"Error: {str(e)}")
        finally:
            if self.pc:
                await self.pc.close()
            logger.debug("WebRTCThread stopped")

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_async())

    def stop(self):
        self.running = False

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
        
        self.test_button = QPushButton("Generate Test Frame")
        self.test_button.clicked.connect(self.generate_test_frame)
        layout.addWidget(self.test_button)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        self.webrtc_thread = WebRTCThread()
        self.webrtc_thread.connection_status.connect(self.update_status)
        self.webrtc_thread.frame_received.connect(self.display_frame)
        self.webrtc_thread.start()
        
        logger.debug("MainWindow initialized")

    def generate_test_frame(self):
        logger.debug("Generating test frame")
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        self.display_frame(img)

    def display_frame(self, img):
        height, width, channel = img.shape
        bytes_per_line = 3 * width
        q_img = QImage(img.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.video_label.setPixmap(pixmap)

    def update_status(self, status):
        self.status_label.setText(f"Status: {status}")
        logger.debug(f"Status updated: {status}")

    def closeEvent(self, event):
        self.webrtc_thread.stop()
        self.webrtc_thread.wait()
        super().closeEvent(event)

if __name__ == "__main__":
    logger.info("Starting application")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())