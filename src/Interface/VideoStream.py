import sys
import websocket
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import pyqtSignal, QObject, QThread
from PyQt5.QtGui import QImage, QPixmap
import os
os.environ['GST_DEBUG'] = '3'

try:
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst, GLib
except ImportError as e:
    print('Gstreamer not found: ', e)
    sys.exit(1)

Gst.init(None)


class VideoStream(QObject):
    frame_received = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self.image_display_widget = QLabel()
        self.ws = websocket.WebSocketApp("ws://localhost:8084",
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self.ws.run_forever)

        self.pipeline = Gst.parse_launch(
            'appsrc name=src ! decodebin ! videoconvert ! videoscale ! appsink name=sink emit-signals=True')
        self.appsrc = self.pipeline.get_by_name('src')
        self.appsink = self.pipeline.get_by_name('sink')
        self.appsink.connect('new-sample', self.on_new_sample)
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_new_sample(self, appsink):
        print('Received new sample')
        sample = appsink.emit('pull-sample')
        buf = sample.get_buffer()
        result, mapinfo = buf.map(Gst.MapFlags.READ)
        image = QImage(mapinfo.data, 640, 480, QImage.Format_RGB888)
        self.frame_received.emit(image)
        buf.unmap(mapinfo)
        self.image_display_widget.setPixmap(QPixmap.fromImage(image))
        return Gst.FlowReturn.OK

    def start(self):
        self.thread.start()

    def on_message(self, ws, message):
        print('Received message: ', len(message))
        buf = Gst.Buffer.new_wrapped(message)
        self.appsrc.emit('push-buffer', buf)

    def on_error(self, ws, error):
        print('WebSocket error: ', error)

    def on_close(self, ws, close_status_code, close_msg, close_headers):
        print('WebSocket close')


class VideoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.video_stream = VideoStream()
        self.video_stream.frame_received.connect(self.handle_frame)
        self.video_stream.start()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.label = QLabel()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.setWindowTitle('Video Stream')

    def handle_frame(self, frame):
        self.label.setPixmap(QPixmap.fromImage(frame))


def main():
    app = QApplication([])
    video_widget = VideoWidget()
    video_widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
