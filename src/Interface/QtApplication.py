from PyQt5.QtWebSockets import QWebSocket, QWebSocketProtocol
from PyQt5.QtCore import QUrl, QJsonDocument, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from ChatApplication import ChatApplication
import numpy as np
import threading


def init_gstreamer():
    import gi
    gi.require_version('Gst', '1.0')
    gi.require_version('GLib', '2.0')
    from gi.repository import Gst, GLib
    Gst.init(None)
    return Gst, GLib


Gst, GLib = init_gstreamer()


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

        self.gst_timer = QTimer()
        self.gst_timer.timeout.connect(self.gst_main_loop)
        self.gst_timer.start(0)

    def gst_main_loop(self):
        GLib.MainContext.default().iteration(False)

    def on_connected(self):
        print("WebSocket connected")
        caps = Gst.Caps.from_string('video/webm;codecs=vp9')
        self.pipeline = Gst.parse_launch(
            'appsrc name=src ! multiqueue ! decodebin ! videoconvert ! appsink name=sink')

        self.appsrc = self.pipeline.get_by_name('src')
        self.appsrc.set_property('caps', caps)
        self.appsink = self.pipeline.get_by_name('sink')
        self.appsink.set_property('emit-signals', True)
        self.appsink.connect('new-sample', self.on_new_sample)
        self.appsink.connect('eos', self.on_eos)
        self.pipeline.set_state(Gst.State.PLAYING)
        self.gst_thread = threading.Thread(target=self.gst_main_loop)
        self.gst_thread.start()

        bus = self.pipeline.get_bus()
        bus.connect("message::error", self.on_error)

    def on_disconnected(self):
        print("WebSocket disconnected")

    def on_binary_message_received(self, message):
        buf = Gst.Buffer.new_wrapped(message)
        ret = self.appsrc.emit('push-buffer', buf)
        if ret == Gst.FlowReturn.OK:
            print('Pushed buffer to GStreamer')
        else:
            print('Push buffer error')

    def on_new_sample(self, appsink):
        print('New sample')
        sample = appsink.emit('pull-sample')
        buf = sample.get_buffer()
        print('Recived frame: ', buf)

        data = buf.extract_dup(0, buf.get_size())
        image = QImage(data, 640, 480, QImage.Format_RGB888)
        self.camera_view.setPixmap(QPixmap.fromImage(image))

        return Gst.FlowReturn.OK

    def on_eos(self, appsink):
        print('End of stream')

    def on_error(self, bus, message):
        err, debug_info = message.parse_error()
        print('GStreamer error:', err, debug_info)
        self.loop.quit()


app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
