import subprocess
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(expand=True, fill="both")
        self.create_widgets()

        self.event_service_process = subprocess.Popen(
            "node src/service/EventService.cjs")

        threading.Thread(target=self.start_wscat, daemon=True).start()

        self.predefined_responses = [
            "/Holi!!", "/Hola, ¿cómo estás?", "/¿En qué puedo ayudarte?"]
        self.predefined_response_buttons = []

    def quit(self):
        self.event_service_process.terminate()
        super().quit()

    def create_widgets(self):
        self.chat_display = ScrolledText(self, state='disabled', height=15)
        self.chat_display.pack(padx=10, pady=10, fill='both', expand=True)

        self.message_frame = tk.Frame(self)
        self.message_frame.pack(fill='x', padx=10, pady=10)

        self.message_input = tk.Entry(self.message_frame)
        self.message_input.pack(side='left', fill='x',
                                expand=True, padx=(0, 10))
        self.message_input.bind(
            "<Return>", lambda e: self.send_message(self.message_input.get()))

        self.send_button = tk.Button(
            self.message_frame, text='Send', command=self.send_message(self.message_input.get()))
        self.send_button.pack(side='right')

    def start_wscat(self):
        wscat_path = "C:/Users/Usuario/AppData/Roaming/npm/wscat.cmd"
        self.process = subprocess.Popen([wscat_path, "-c", "ws://localhost:8081"], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)

        for line in iter(self.process.stdout.readline, ''):
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, line)
            self.chat_display.see(tk.END)
            self.chat_display.config(state='disabled')

            if not self.predefined_response_buttons:
                self.display_predefined_response()

    def display_predefined_response(self):
        for response in self.predefined_responses:
            button = tk.Button(
                self, text=response, command=lambda response=response: self.send_predefined_response(response))
            button.pack()
            self.predefined_response_buttons.append(button)

    def send_predefined_response(self, response):
        self.send_message(response)
        for button in self.predefined_response_buttons:
            button.destroy()
        self.predefined_response_buttons = []

    def send_message(self, message):
        if message.strip() != "":
            self.display_message("SHARA: " + message)
            message += "\n"
            self.process.stdin.write(message)
            self.process.stdin.flush()
            self.message_input.delete(0, 'end')

    def display_message(self, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert('end', message + "\n")
        self.chat_display.see('end')
        self.chat_display.config(state='disabled')


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.master.title("Chat-like Application")
    app.mainloop()
