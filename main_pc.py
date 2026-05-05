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

#Clase para la pantalla de inicio
class PantallaInicio(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        tk.Label(self, text="StrangerTEC", fg="red").pack(pady=30)
        tk.Label(self, text="Morse Translator", fg="gray").pack()

        tk.Button(self, text="Iniciar juego", width=20, bg="green", fg="white", command=self.app.iniciar_juego).pack(pady=20)

        tk.Button(self, text="Editar frases", width=20, bg="orange", fg="white", command=self.app.editor_frases).pack(pady=5)

#Clase para la GIU del juego
class PantallaJuego(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.press_time = None
        self.is_pressed = False
        self.unit_time = 0.3
        self.buffer = []
        self.text = []
        self.timer = None
        self.word_timer = None
        self.puntaje = 0
        self.serial_port = None
        self.puntaje_a = 0
        self.puntaje_b = 0
        self.turno = "A"

        self.label_turno = tk.Label(self, text="Turno: Jugador A (teclado)")
        self.label_turno.pack(pady=5)

        self.frase_objetivo = ""
        self.label_objetivo = tk.Label(self, text=f"Escriba en Morse: {self.frase_objetivo}", fg="red")
        self.label_objetivo.pack(pady=10)

        self.label_morse = tk.Label(self, text="")
        self.label_morse.pack(pady=20)

        self.label_text = tk.Label(self, text="")
        self.label_text.pack(pady=20)

        info = tk.Label(self, text="Espacio = punto/raya y Pausa = nueva letra")
        info.pack()

        self.label_puntaje = tk.Label(self, text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
        self.label_puntaje.pack(pady=5)

        self.label_resultado = tk.Label(self, text="", fg="orange")
        self.label_resultado.pack(pady=5)

        self.label_serial = tk.Label(self, text="Maqueta: desconectada", fg="gray")
        self.label_serial.pack()

        #Botones
        frame_botones = tk.Frame(self)
        frame_botones.pack(pady=10)

        self.btn_nueva = tk.Button(frame_botones, text="Nueva ronda", command=self.nueva_ronda)
        self.btn_nueva.pack(pady=10)

        self.volver_menu = tk.Button(frame_botones, text="Menú principal", command=self.app.volver_inicio)
        self.volver_menu.pack(side=tk.LEFT, padx=5)

        #Bindings del space
        parent.bind("<KeyPress-space>", self.key_press)
        parent.bind("<KeyRelease-space>", self.key_release)

    def iniciar(self):
        self.puntaje_a = 0
        self.puntaje_b = 0
        self.turno = "A"
        self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
        self.label_turno.config(text="Turno: Jugador A (teclado)")
        self.label_resultado.config(text="")
        self.nueva_ronda()
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
            self.app.root.after_cancel(self.timer)

        self.timer = self.app.root.after(int(4 * self.unit_time * 1000), self.decode_letter)
        self.word_timer = self.app.root.after(int(8 * self.unit_time * 1000), self.add_space)

    def decode_letter(self):
        code = "".join(self.buffer)
        char = MORSE.get(code, "?")

        self.text.append(char)
        self.label_text.config(text="".join(self.text))

        self.buffer = []
        self.label_morse.config(text="")

        if hasattr(self, "word_timer") and self.word_timer: #Revisa si tiene el atributo word_timer y si existe un timer activo
            self.app.root.after_cancel(self.word_timer)
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
        self.frase_objetivo = random.choice(self.app.frases)
        self.label_objetivo.config(text=f"Escriba en Morse: {self.frase_objetivo}")
        self.text = []
        self.buffer = []
        self.label_morse.config(text="")
        self.label_text.config(text="")
        self.label_resultado.config(text="")
        if self.timer:
            self.app.root.after_cancel(self.timer)
        if self.word_timer:
            self.app.root.after_cancel(self.word_timer)

    def cambiar_turno(self):
        self.text = []
        self.buffer = []
        self.label_morse.config(text="")
        self.label_text.config(text="")
        self.turno = "B"
        self.label_turno.config(text="Turno: Jugador B (maqueta)")
        self.enviar_frase()

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
        if self.serial_port and self.serial_port.is_open:
            return
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
                    self.app.root.after(0, self.recibir_simbolo, ".")
                elif linea == "DASH":
                    self.app.root.after(0, self.recibir_simbolo, "-")
            except Exception:
                break

    def recibir_simbolo(self, simbolo: str):
        if self.turno != "B":
            return
        self.buffer.append(simbolo)
        self.update_morse()
        self.reset_timer()

    def enviar_frase(self):
        if self.serial_port and self.serial_port.is_open:
            mensaje = f"FRASE:{self.frase_objetivo}\n"
            self.serial_port.write(mensaje.encode("utf-8"))

    def editor_frases(self):
        win = tk.Toplevel(self.root)
        win.title("Editar frases")
        win.geometry("350x420")
        win.resizable(False, False)

        tk.Label(win, text="Edite las frases (máx. 16 caracteres cada una)").pack(pady=5)

        entries = []
        for i, frase in enumerate(self.frases):
            frame = tk.Frame(win)
            frame.pack(fill=tk.X, padx=15, pady=2)

            tk.Label(frame, text=f"{i+1}.", width=3).pack(side=tk.LEFT)

            var = tk.StringVar(value=frase)
            entry = tk.Entry(frame, textvariable=var, width=20)
            entry.pack(side=tk.LEFT, padx=5)

            # Contador de caracteres en tiempo real
            contador = tk.Label(frame, text=f"{len(frase)}/16", width=6,fg="green" if len(frase) <= 16 else "red")
            contador.pack(side=tk.LEFT)

            def actualizar_contador(var=var, contador=contador):
                texto = var.get().upper()
                largo = len(texto)
                contador.config(text=f"{largo}/16",fg="green" if largo <= 16 else "red")
            var.trace_add("write", lambda *args, v=var, c=contador: actualizar_contador(v, c)) #detecta cambios en el entry y actualiza el contador

            entries.append(var)

        # Mensaje de error
        label_error = tk.Label(win, text="", fg="red")
        label_error.pack(pady=3)

        def guardar():
            nuevas = []
            for i, var in enumerate(entries):
                texto = var.get().strip().upper()
                if len(texto) == 0:
                    label_error.config(text=f"La frase {i+1} está vacía.")
                    return
                if len(texto) > 16:
                    label_error.config(text=f"La frase {i+1} supera los 16 caracteres.")
                    return
                nuevas.append(texto)
            self.frases = nuevas
            win.destroy()

        def cancelar():
            win.destroy()

        frame_btns = tk.Frame(win)
        frame_btns.pack(pady=10)
        tk.Button(frame_btns, text="Guardar", command=guardar, bg="green", fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_btns, text="Cancelar", command=cancelar, bg="red", fg="white", width=10).pack(side=tk.LEFT, padx=5)

#Clase principal de la aplicación
class MorseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("StrangerTEC - Morse")
        self.root.geometry("500x400")

        self.frases = FRASES[:]  #Copia de la lista original para modificarla sin afectar la constante

        self.pantalla_inicio = PantallaInicio(root, self)
        self.pantalla_juego  = PantallaJuego(root, self)

        self.mostrar(self.pantalla_inicio)

    def mostrar(self, pantalla):
        self.pantalla_inicio.pack_forget()
        self.pantalla_juego.pack_forget()
        pantalla.pack(fill=tk.BOTH, expand=True)

    def iniciar_juego(self):
        self.mostrar(self.pantalla_juego)
        self.pantalla_juego.iniciar()

    def volver_inicio(self):
        self.mostrar(self.pantalla_inicio)

    def editor_frases(self):
        win = tk.Toplevel(self.root)
        win.title("Editar frases")
        win.geometry("350x420")
        win.resizable(False, False)

        tk.Label(win, text="Edite las frases (máx. 16 caracteres cada una)").pack(pady=5)

        entries = []
        for i, frase in enumerate(self.frases):
            frame = tk.Frame(win)
            frame.pack(fill=tk.X, padx=15, pady=2)
            tk.Label(frame, text=f"{i+1}.", width=3).pack(side=tk.LEFT)
            var = tk.StringVar(value=frase)
            tk.Entry(frame, textvariable=var, width=20).pack(side=tk.LEFT, padx=5)
            contador = tk.Label(frame, text=f"{len(frase)}/16", width=6,
                                 fg="green" if len(frase) <= 16 else "red")
            contador.pack(side=tk.LEFT)
            def actualizar(var=var, contador=contador):
                largo = len(var.get())
                contador.config(text=f"{largo}/16", fg="green" if largo <= 16 else "red")
            var.trace_add("write", lambda *args, v=var, c=contador: actualizar(v, c))
            entries.append(var)

        label_error = tk.Label(win, text="", fg="red")
        label_error.pack(pady=3)

        def guardar():
            nuevas = []
            for i, var in enumerate(entries):
                texto = var.get().strip().upper()
                if len(texto) == 0:
                    label_error.config(text=f"La frase {i+1} está vacía.")
                    return
                if len(texto) > 16:
                    label_error.config(text=f"La frase {i+1} supera los 16 caracteres.")
                    return
                nuevas.append(texto)
            self.frases = nuevas
            win.destroy()

        frame_btns = tk.Frame(win)
        frame_btns.pack(pady=10)
        tk.Button(frame_btns, text="Guardar", command=guardar, bg="green", fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_btns, text="Cancelar", command=win.destroy, bg="red", fg="white", width=10).pack(side=tk.LEFT, padx=5)

#Correr la aplicación
root = tk.Tk()
app = MorseApp(root)
root.mainloop()