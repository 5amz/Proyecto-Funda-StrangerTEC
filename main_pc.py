import tkinter as tk
import time
import random
import threading
import serial
import serial.tools.list_ports

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
        self.serial_port = None
        self.puntaje_a = 0
        self.puntaje_b = 0
        self.turno = "A"

        self.label_turno = tk.Label(root, text="Turno: Jugador A (teclado)")
        self.label_turno.pack(pady=5)

        self.frase_objetivo = random.choice(FRASES)
        self.label_objetivo = tk.Label(root, text=f"Escriba en Morse: {self.frase_objetivo}", fg="red")
        self.label_objetivo.pack(pady=10)

        self.label_morse = tk.Label(root, text="")
        self.label_morse.pack(pady=20)

        self.label_text = tk.Label(root, text="")
        self.label_text.pack(pady=20)

        info = tk.Label(root, text="Espacio = punto/raya y Pausa = nueva letra")
        info.pack()

        self.label_puntaje = tk.Label(root, text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
        self.label_puntaje.pack(pady=5)

        self.label_resultado = tk.Label(root, text="", fg="orange")
        self.label_resultado.pack(pady=5)

        self.label_serial = tk.Label(root, text="Maqueta: desconectada", fg="gray")
        self.label_serial.pack()

        #Botones
        self.btn_nueva = tk.Button(root, text="Nueva ronda", command=self.nueva_ronda)
        self.btn_nueva.pack(pady=10)

        #Bindings del space
        root.bind("<KeyPress-space>", self.key_press)
        root.bind("<KeyRelease-space>", self.key_release)

        self.conectar_serial()

    def key_press(self, event):
        if self.turno != "A":
            return
        if self.is_pressed:
            return
        self.is_pressed = True
        self.press_time = time.time()

    def key_release(self, event):
        if self.turno != "A":
            return
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

        self.timer = self.root.after(int(4 * self.unit_time * 1000), self.decode_letter)
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

        if self.turno == "A":
            self.puntaje_a += correctos
            self.label_resultado.config(text=f"Jugador A: {respuesta}  →  {correctos}/{total} letras bien")
            self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
            self.cambiar_turno()
        else:
            self.puntaje_b += correctos
            self.label_resultado.config(text=f"Jugador B: {respuesta}  →  {correctos}/{total} letras bien")
            self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
            self.mostrar_ganador()

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

    def cambiar_turno(self):
        self.text = []
        self.buffer = []
        self.label_morse.config(text="")
        self.label_text.config(text="")
        self.turno = "B"
        self.label_turno.config(text="Turno: Jugador B (maqueta)")

    def mostrar_ganador(self):
        if self.puntaje_a > self.puntaje_b:
            ganador = "¡Ganó Jugador A!"
        elif self.puntaje_b > self.puntaje_a:
            ganador = "¡Ganó Jugador B!"
        else:
            ganador = "¡Empate!"
        self.label_resultado.config(text=f"{ganador}  —  A: {self.puntaje_a} | B: {self.puntaje_b}")
        self.turno = "A"
        self.label_turno.config(text="Turno: Jugador A (teclado) — Presione Nueva ronda")

    def conectar_serial(self):
        puertos = serial.tools.list_ports.comports()
        for p in puertos:
            if "USB" in p.description or "Pico" in p.description:
                try:
                    self.serial_port = serial.Serial(p.device, 115200, timeout=1)
                    self.label_serial.config(text=f"Maqueta: conectada ({p.device})", fg="green")
                    hilo = threading.Thread(target=self.leer_serial, daemon=True)
                    hilo.start()
                    return
                except Exception:
                    pass
        self.label_serial.config(text="Maqueta: no encontrada — solo teclado", fg="red")

    def leer_serial(self):
        while self.serial_port and self.serial_port.is_open:
            try:
                linea = self.serial_port.readline().decode("utf-8").strip()
                if linea == "DOT":
                    self.root.after(0, self.recibir_simbolo, ".")
                elif linea == "DASH":
                    self.root.after(0, self.recibir_simbolo, "-")
            except Exception:
                break

    def recibir_simbolo(self, simbolo: str):
        if self.turno != "B":
            return
        self.buffer.append(simbolo)
        self.update_morse()
        self.reset_timer()

#Correr la aplicación
root = tk.Tk()
app = MorseApp(root)
root.mainloop()