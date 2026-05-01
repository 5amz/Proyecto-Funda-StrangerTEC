import tkinter as tk
import time

# Diccionario Morse básico
MORSE = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D",
    ".": "E", "..-.": "F", "--.": "G", "....": "H",
    "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N", "---": "O", ".--.": "P",
    "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z", "-----": "0", ".----": "1", 
    "..---": "2", "...--": "3", "....-": "4", ".....": "5",
    "-....": "6", "--...": "7", "---..": "8", "----.": "9",
    ".-.-.":"+", "-....-": "-"
}

#Clase para la GIU del juego
class MorseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("StrangerTEC - Morse")
        self.root.geometry("500x300")

        self.press_time = None
        self.is_pressed = False
        self.unit_time = 0.3
        self.buffer = []
        self.text = []
        self.timer = None

        self.label_morse = tk.Label(root, text="")
        self.label_morse.pack(pady=20)

        self.label_text = tk.Label(root, text="")
        self.label_text.pack(pady=20)

        info = tk.Label(root, text="Espacio = punto/raya y Pausa = nueva letra")
        info.pack()

        #Bindings del space
        root.bind("<KeyPress-space>", self.key_press)
        root.bind("<KeyRelease-space>", self.key_release)

    def key_press(self, event):
        if self.is_pressed:
            return
        
        self.is_pressed = True
        self.press_time = time.time()

    def key_release(self, event):
        if not self.is_pressed:
            return

        duration = time.time() - self.press_time

        if duration < self.unit_time:
            symbol = "."
        else:
            symbol = "-"

        self.buffer.append(symbol)
        self.update_morse()
        self.reset_timer()
        
        self.press_time = None
        self.is_pressed = False

    def reset_timer(self):
        if self.timer:
            self.root.after_cancel(self.timer)

        self.timer = self.root.after(int(5 * self.unit_time * 1000), self.decode_letter)

    def decode_letter(self):
        code = "".join(self.buffer)
        char = MORSE.get(code, "?")

        self.text.append(char)
        self.label_text.config(text="".join(self.text))

        self.buffer = []
        self.label_morse.config(text="")

    def update_morse(self):
        self.label_morse.config(text="".join(self.buffer))

#Correr la aplicación
root = tk.Tk()
app = MorseApp(root)
root.mainloop()