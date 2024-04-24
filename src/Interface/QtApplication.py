from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from ChatApplication import ChatApplication
import numpy as np


def init_gstreamer():
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    Gst.init(None)
    return Gst


Gst = init_gstreamer()


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Mi Aplicación")

        # self.event_service_process = subprocess.Popen(
        #     ['node', 'src/service/EventService.cjs'])

        widget = QWidget(self)
        self.setCentralWidget(widget)

        layout = QVBoxLayout()
        widget.setLayout(layout)

        web_view = QWebEngineView()
        web_view.load(QUrl("http://localhost:5173/"))
        layout.addWidget(web_view)

        self.buffer = bytearray()

        self.camera_view = QLabel()
        layout.addWidget(self.camera_view)

        self.websocket = QWebSocket()
        self.websocket.binaryMessageReceived.connect(
            self.on_binary_message_received)
        self.websocket.error.connect(self.on_error)
        self.websocket.connected.connect(self.on_connected)
        self.websocket.disconnected.connect(self.on_disconnected)
        self.websocket.open(QUrl("ws://localhost:8084"))

        self.chat_app = ChatApplication()
        layout.addWidget(self.chat_app)

    def on_connected(self):
        print("WebSocket connected")
        caps = Gst.Caps.from_string('video/webm;codecs=vp9')
        self.pipeline = Gst.parse_launch(
            'appsrc name=src ! decodebin ! videoconvert ! videoscale ! appsink name=sink emit-signals=True')

        self.appsrc = self.pipeline.get_by_name('src')
        self.appsrc.set_property('caps', caps)
        self.appsink = self.pipeline.get_by_name('sink')
        self.appsink.connect('new-sample', self.on_new_sample)
        self.pipeline.set_state(Gst.State.PLAYING)

        bus = self.pipeline.get_bus()
        bus.connect("message::error", self.on_error)

    def on_disconnected(self):
        print("WebSocket disconnected")

    def on_binary_message_received(self, message):
        buf = Gst.Buffer.new_wrapped(message)
        self.appsrc.emit('push-buffer', buf)

    def on_new_sample(self, appsink):
        print('New sample')
        sample = appsink.emit('pull-sample')
        buf = sample.get_buffer()

        result, mapinfo = buf.map(Gst.MapFlags.READ)
        image = QImage(mapinfo.data, 640, 480, QImage.Format_RGB888)
        buf.unmap(mapinfo)
        print('Buffer unmapped')
        self.camera_view.setPixmap(QPixmap.fromImage(image))
        print('Image displayed')

        return Gst.FlowReturn.OK

    def on_error(self, bus, message):
        err, debug_info = message.parse_error()
        print('GStreamer error:', err, debug_info)
        self.loop.quit()


app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
