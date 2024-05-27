from PyQt5.QtCore import QThread, pyqtSignal
import socketio


class WebSocketClient(QThread):
    message_received = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()
        self.sio = socketio.Client()

        @self.sio.event
        def connect():
            print("Connected to the server")

        @self.sio.event
        def disconnect():
            print("Disconnected from the server")

        @self.sio.on('video_chunk')
        def on_message(data):
            data_bytes = bytes(data, 'utf-8')
            self.message_received.emit(data_bytes)

    def run(self):
        print("Connecting to the server")
        self.sio.connect('http://localhost:3000')
        self.sio.wait()
