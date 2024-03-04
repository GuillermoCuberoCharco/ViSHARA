import tkinter as tk
import threading
import sys
from PyQt5.QtWidgets import QApplication


root = tk.Tk()
root.title("Aplicación de control para web")
root.geometry('1280x720')


def create_mock_frame(container, text, row, column):
    frame = tk.LabelFrame(container, text=text, bd=2)
    frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")
    return frame


for i in range(3):
    root.grid_columnconfigure(i, weight=1)
for i in range(2):
    root.grid_rowconfigure(i, weight=1)

user_emotion_analysis_frame = create_mock_frame(
    root, "Análisis de emociones del usuario", 0, 0)
webcam_frame = create_mock_frame(
    root, "Cámara del usuario capturada desde la Web", 0, 1)

pending_features_frame = create_mock_frame(
    root, "Funcionalidades (Pendiente de especificar)", 1, 1)
shara_response_frame = create_mock_frame(
    root, "Respuesta autogenerada con SHARA", 1, 2)

root.mainloop()
