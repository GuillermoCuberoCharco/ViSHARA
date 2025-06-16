from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import pyaudio
import wave
import threading
import io
from utils.logger import get_logger

logger = get_logger(__name__)

class VoiceRecorderWidget(QWidget):
    """Widget para grabar audio desde el micrófono"""

    recording_finished = pyqtSignal(bytes)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_recording = False
        self.audio_data = bytearray()
        self.recording_thread = None
        self.pyaudio_instance = None
        self.stream = None

        # Configuración de audio
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024

        self._setup_ui()
        self._init_audio()

    def _setup_ui(self):
        """Configura la interfaz de usuario del widget."""
        layout = QVBoxLayout(self)

        # Botón de grabación
        self.record_button = QPushButton("🎤 Iniciar Grabación")
        self.record_button.setMinimumHeight(40)
        self.record_button.clicked.connect(self._toggle_recording)
        self.record_button.setStyleSheet("""
        QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        layout.addWidget(self.record_button)

        # Etiqueta de estado
        self.status_label = QLabel("Listo para grabar")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def _init_audio(self):
        """Inicializa PyAudio."""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
        except Exception as e:
            logger.error(f"Error al inicializar PyAudio: {e}")

    def _toggle_recording(self):
        """Inicia o detiene la grabación de audio."""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Inicia grabación en un hilo separado."""
        try:
            self.audio_data.clear()
            self.is_recording = True
            
            self.stream = self.pyaudio_instance.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            self.record_button.setText("⏹️ Detener")
            self.record_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px;
                    font-weight: bold;
                }
            """)
            self.status_label.setText("🔴 Grabando...")
            
            # Iniciar thread de grabación
            self.recording_thread = threading.Thread(target=self._record_worker)
            self.recording_thread.start()
            
        except Exception as e:
            logger.error(f"Error iniciando grabación: {e}")

    def _stop_recording(self):
        """Detiene grabación."""
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        self.record_button.setText("🎤 Iniciar Grabación")
        self.record_button.setStyleSheet("")
        self.status_label.setText("Procesando...")
        
        # Convertir a WAV y emitir
        wav_data = self._to_wav()
        self.recording_finished.emit(wav_data)
        
        self.status_label.setText("Listo para grabar")

    def _record_worker(self):
        """Worker para grabar audio en un hilo separado."""
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk)
                self.audio_data.extend(data)
            except Exception as e:
                break

    def _to_wav(self) -> bytes:
        """Convierte los datos grabados a formato WAV."""
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.pyaudio_instance.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(bytes(self.audio_data))
        return wav_buffer.getvalue()

    def cleanup(self):
        """Limpia recursos."""
        if self.is_recording:
            self._stop_recording()
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()