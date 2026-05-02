import tkinter as tk
import time
import random

FRASES = ["SOS", "SI", "NO", "HOLA", "TEC", "MORSE", "WILL", "UPSIDE DOWN", "STRANGER", "JOYCE"]

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
        self.puntaje = 0

        self.frase_objetivo = random.choice(FRASES)
        self.label_objetivo = tk.Label(root, text=f"Escriba en Morse: {self.frase_objetivo}", fg="red")
        self.label_objetivo.pack(pady=10)

        self.label_morse = tk.Label(root, text="")
        self.label_morse.pack(pady=20)

        self.label_text = tk.Label(root, text="")
        self.label_text.pack(pady=20)

        info = tk.Label(root, text="Espacio = punto/raya y Pausa = nueva letra")
        info.pack()

        self.label_puntaje = tk.Label(root, text="Puntaje: 0", fg="green")
        self.label_puntaje.pack(pady=5)

        self.label_resultado = tk.Label(root, text="", fg="orange")
        self.label_resultado.pack(pady=5)

        #Botones
        self.btn_nueva = tk.Button(root, text="Nueva ronda", command=self.nueva_ronda)
        self.btn_nueva.pack(pady=10)

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
        self.word_timer = self.root.after(int(8 * self.unit_time * 1000), self.add_space)

    def decode_letter(self):
        code = "".join(self.buffer)
        char = MORSE.get(code, "?")

        self.text.append(char)
        self.label_text.config(text="".join(self.text))

        self.buffer = []
        self.label_morse.config(text="")

        if hasattr(self, "word_timer") and self.word_timer: #Revisa si tiene el atributo word_timer y si existe un timer activo
            self.root.after_cancel(self.word_timer)
            self.word_timer = None

        texto_actual = "".join(self.text).strip()
        if len(texto_actual.replace(" ", "")) >= len(self.frase_objetivo.replace(" ", "")):
            self.evaluar()

    def evaluar(self):
        respuesta = "".join(self.text).strip().upper()
        objetivo  = self.frase_objetivo.upper()
        correctos = sum(1 for a, b in zip(objetivo.replace(" ", ""), respuesta.replace(" ", "")) if a == b) #Combinar ambas frases y comparar las letras
        total = len(objetivo.replace(" ", ""))
        self.puntaje += correctos
        self.label_puntaje.config(text=f"Puntaje: {self.puntaje}")
        self.label_resultado.config(text=f"Correcto: {respuesta}  →  {correctos}/{total} letras bien")

    def add_space(self):
        if self.text and self.text[-1] != " ":
            self.text.append(" ")
            self.label_text.config(text="".join(self.text)) 

    def update_morse(self):
        self.label_morse.config(text="".join(self.buffer))

    def nueva_ronda(self):
        self.frase_objetivo = random.choice(FRASES)
        self.label_objetivo.config(text=f"Escriba en Morse: {self.frase_objetivo}")
        self.text = []
        self.buffer = []
        self.label_morse.config(text="")
        self.label_text.config(text="")
        self.label_resultado.config(text="")
        if self.timer:
            self.root.after_cancel(self.timer)
        if self.word_timer:
            self.root.after_cancel(self.word_timer)

#Correr la aplicación
root = tk.Tk()
app = MorseApp(root)
root.mainloop()