from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QComboBox, QGroupBox)

class WatsonResponseDialog(QDialog):
    @staticmethod
    def get_all_states():
        return ['Attention', 'Hello', 'No', 'Yes', 'Angry', 'Sad', 'Joy', 'Blush']
    
    # Preset responses for each state
    @staticmethod
    def get_preset_responses():
        return {
            'Attention': [
                "Estoy prestando atención a lo que dices.",
                "Me interesa mucho este tema.",
                "Continúa, te escucho atentamente.",
                "Entiendo tu punto de vista."
            ],
            'Hello': [
                "¡Hola! ¿Cómo estás hoy?",
                "¡Qué gusto verte de nuevo!",
                "¡Bienvenido/a!",
                "¡Hola! Espero que estés teniendo un buen día."
            ],
            'No': [
                "Lo siento, pero no puedo hacer eso.",
                "Me temo que eso no es posible.",
                "Desafortunadamente, no es viable.",
                "No, pero podríamos buscar una alternativa."
            ],
            'Yes': [
                "¡Sí, por supuesto!",
                "Me parece una excelente idea.",
                "Estoy de acuerdo contigo.",
                "Definitivamente podemos hacer eso."
            ],
            'Angry': [
                "Entiendo tu frustración.",
                "Comprendo que esto puede ser molesto.",
                "Vamos a resolver esto juntos.",
                "Tu molestia es válida, busquemos una solución."
            ],
            'Sad': [
                "Lamento que te sientas así.",
                "Estoy aquí para escucharte.",
                "Comprendo que es una situación difícil.",
                "¿Cómo puedo ayudarte a sentirte mejor?"
            ],
            'Joy': [
                "¡Me alegro mucho por ti!",
                "¡Esas son excelentes noticias!",
                "¡Qué maravilloso momento!",
                "¡Comparto tu felicidad!"
            ],
            'Blush': [
                "Me siento halagado/a.",
                "Gracias por tus amables palabras.",
                "Eres muy amable al decir eso.",
                "Me alegra que valores mi ayuda."
            ]
        }

    def __init__(self, response, current_state, parent=None):
        super(WatsonResponseDialog, self).__init__(parent)
        self.response = response
        self.current_state = current_state
        self.preset_responses = self.get_preset_responses()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Watson Response')
        self.setMinimumWidth(600)
        layout = QVBoxLayout()

        # Watson response section
        response_group = QGroupBox("Respuesta Actual")
        response_layout = QVBoxLayout()
        response_label = QLabel(f"[Emotion detected: {self.current_state}]")
        self.response_edit = QTextEdit(self.response)
        response_layout.addWidget(response_label)
        response_layout.addWidget(self.response_edit)
        response_group.setLayout(response_layout)
        layout.addWidget(response_group)

        # Robot states section
        states_group = QGroupBox("Estados Emocionales")
        states_layout = QVBoxLayout()
        
        buttons_layout = QHBoxLayout()
        self.state_buttons = {}
        for state in self.get_all_states():
            button = QPushButton(state)
            button.setCheckable(True)
            button.clicked.connect(self.update_state)
            buttons_layout.addWidget(button)
            self.state_buttons[state] = button
        
        states_layout.addLayout(buttons_layout)
        states_group.setLayout(states_layout)
        layout.addWidget(states_group)

        # Preset responses section
        preset_group = QGroupBox("Respuestas Predefinidas")
        preset_layout = QVBoxLayout()
        
        self.preset_combo = QComboBox()
        self.update_preset_responses(self.current_state)
        self.preset_combo.currentTextChanged.connect(self.update_response)
        
        preset_layout.addWidget(self.preset_combo)
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # Action buttons
        button_layout = QHBoxLayout()
        send_button = QPushButton('Enviar')
        send_button.clicked.connect(self.accept)
        cancel_button = QPushButton('Cancelar')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(send_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Set initial state
        if self.current_state in self.state_buttons:
            self.state_buttons[self.current_state].setChecked(True)
        else:
            self.state_buttons['Attention'].setChecked(True)

    def update_state(self):
        sender_button = self.sender()
        for button in self.state_buttons.values():
            if button != sender_button:
                button.setChecked(False)
        
        new_state = self.get_state()
        self.update_preset_responses(new_state)

    def update_preset_responses(self, state):
        self.preset_combo.clear()
        self.preset_combo.addItem("-- Selecciona una respuesta predefinida --")
        if state in self.preset_responses:
            self.preset_combo.addItems(self.preset_responses[state])

    def update_response(self, new_text):
        if new_text and new_text != "-- Selecciona una respuesta predefinida --":
            self.response_edit.setText(new_text)

    def get_response(self):
        return self.response_edit.toPlainText()

    def get_state(self):
        for state, button in self.state_buttons.items():
            if button.isChecked():
                return state
        return 'Attention'