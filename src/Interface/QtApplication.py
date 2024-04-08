from ChatApplication import ChatApplication
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QMessageBox
from PyQt5.QtGui import QPixmap, QImage, QTextCursor
from PyQt5.QtCore import QUrl
import sys
#fmt: off
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
#fmt: on
Gst.init(None)


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Mi Aplicación")

        widget = QWidget(self)
        self.setCentralWidget(widget)

        layout = QVBoxLayout()
        widget.setLayout(layout)

        web_view = QWebEngineView()
        web_view.load(QUrl("http://localhost:5173/"))
        layout.addWidget(web_view)

        chat_app = ChatApplication()
        layout.addWidget(chat_app)

        self.camera_view = QLabel()
        layout.addWidget(self.camera_view)

        self.pipeline = Gst.parse_launch(
            "udpsrc port=5000 ! application/x-rtp, encoding-name=JPEG, payload=26 ! rtpjpegdepay ! jpegdec ! videoconvert ! appsink")

        if not self.pipeline:
            print("Failed to create pipeline")
        else:
            self.appsink = self.pipeline.get_by_name("appsink")

            if not self.appsink:
                print("Failed to get appsink")
            else:
                self.appsink.set_property("emit-signals", True)
                self.appsink.connect("new-sample", self.on_new_sample)
                self.pipeline.set_state(Gst.State.PLAYING)

    def on_new_sample(self, sink):
        sample = sink.emit("pull-sample")
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        print(caps.get_structure(0).get_value("format"))
        print(caps.get_structure(0).get_value("height"))
        print(caps.get_structure(0).get_value("width"))
        print(buffer.get_size())

        image = QImage(buffer.extract_dup(0, buffer.get_size()), caps.get_structure(
            0).get_value("width"), caps.get_structure(0).get_value("height"), QImage.Format_RGB888)
        self.camera_view.setPixmap(QPixmap.fromImage(image))

        return Gst.FlowReturn.OK


app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
