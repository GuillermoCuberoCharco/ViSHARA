import asyncio
import websockets
from PyQt5.QtCore import QThread, pyqtSignal, QByteArray


class WebSocketThread(QThread):
    message_received = pyqtSignal(QByteArray)

    async def connect(self):
        while True:
            try:
                async with websockets.connect("ws://localhost:8083") as websocket:
                    while True:
                        message = await websocket.recv()
                        self.message_received.emit(message)
            except ConnectionRefusedError:
                print("Connection refused, retrying in 1 seconds")
                await asyncio.sleep(1)

    def run(self):
        asyncio.run(self.connect())
