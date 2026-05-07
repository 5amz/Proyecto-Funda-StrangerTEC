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

MORSE_INV = {v: k for k, v in MORSE.items()}

TOTAL_RONDAS = 3

#Clase para la pantalla de inicio
class PantallaInicio(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        tk.Label(self, text="StrangerTEC", fg="red").pack(pady=30)
        tk.Label(self, text="Morse Translator", fg="gray").pack()

        tk.Label(self, text="Modo de presentación:").pack(pady=(15, 0))
        self.modo_var = tk.StringVar(value="ambos")

        tk.Radiobutton(self, text="Solo luces (LEDs)", variable=self.modo_var, value="leds").pack()
        tk.Radiobutton(self, text="Solo sonido (buzzer)", variable=self.modo_var, value="sonido").pack()
        tk.Radiobutton(self, text="Luces y sonido", variable=self.modo_var, value="ambos").pack()

        tk.Button(self, text="Iniciar juego", width=20, bg="green", fg="white", command=self.iniciar).pack(pady=20)

        tk.Button(self, text="Editar frases", width=20, bg="orange", fg="white", command=self.app.editor_frases).pack(pady=5)

    def iniciar(self):
        self.app.presentacion = self.modo_var.get()
        self.app.iniciar_juego()

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
        self.morse_ingresado = []
        self.timer = None
        self.word_timer = None
        self.puntaje = 0
        self.serial_port = None
        self.puntaje_a = 0
        self.puntaje_b = 0
        self.turno = "A"
        self.ronda_actual = 0
        self.ronda_curso = False

        self.label_ronda = tk.Label(self, text=f"Ronda 1 de {TOTAL_RONDAS}")
        self.label_ronda.pack()

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

        self.btn_randomizar = tk.Button(frame_botones, text="Randomizar frase",command=self.randomizar_frase)
        self.btn_randomizar.pack(side=tk.LEFT, padx=5)

        self.btn_enviar = tk.Button(frame_botones, text="Enviar frase", command=self.enviar_frase, state=tk.DISABLED)
        self.btn_enviar.pack(side=tk.LEFT, padx=5)

        self.btn_nueva = tk.Button(frame_botones, text="Nueva ronda", command=self.nueva_ronda, state=tk.DISABLED)
        self.btn_nueva.pack(side=tk.LEFT, padx=5)

        self.volver_menu = tk.Button(frame_botones, text="Menú principal", command=self.app.volver_inicio)
        self.volver_menu.pack(side=tk.LEFT, padx=5)

        #Bindings del space
        #parent.bind("<KeyPress-space>", self.key_press)
        #parent.bind("<KeyRelease-space>", self.key_release)

    def iniciar(self):
        self.puntaje_a = 0
        self.puntaje_b = 0
        self.ronda_actual = 0
        self.turno = "A"
        self.fase = 1
        self.ronda_curso = False
        self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
        self.label_turno.config(text="Turno: Jugador A (teclado)")
        self.label_resultado.config(text="")
        self.bloquear_input()
        self.nueva_ronda()
        self.conectar_serial()

    def key_press(self, event):
        jugador_teclado = "A" if self.fase == 1 else "B"
        if self.turno != jugador_teclado:
            return
        if self.is_pressed:
            return
        self.is_pressed = True
        self.press_time = time.time()

    def key_release(self, event):
        jugador_teclado = "A" if self.fase == 1 else "B"
        if self.turno != jugador_teclado:
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

    def bloquear_input(self):
        self.app.root.unbind("<KeyPress-space>")
        self.app.root.unbind("<KeyRelease-space>")

    def desbloquear_input(self):
        self.app.root.bind("<KeyPress-space>", self.key_press)
        self.app.root.bind("<KeyRelease-space>", self.key_release)

    def randomizar_frase(self):
        if not self.ronda_curso:
            self.frase_objetivo = random.choice(self.app.frases)
            self.label_objetivo.config(text=f"Escriba en Morse: {self.frase_objetivo}")

    def enviar_frase(self):
        if self.serial_port and self.serial_port.is_open:
            modo = self.app.presentacion
            mensaje = f"FRASE:{self.frase_objetivo}:{modo}\n"
            self.serial_port.write(mensaje.encode("utf-8"))
        self.btn_randomizar.config(state=tk.DISABLED)
        self.btn_enviar.config(state=tk.DISABLED)
        self.ronda_curso = True
        self.desbloquear_input()

    def reset_timer(self):
        if self.timer:
            self.app.root.after_cancel(self.timer)

        self.timer = self.app.root.after(int(4 * self.unit_time * 1000), self.decode_letter)
        self.word_timer = self.app.root.after(int(8 * self.unit_time * 1000), self.add_space)

    def decode_letter(self):
        code = "".join(self.buffer)
        char = MORSE.get(code, "?")
        self.morse_ingresado.append(code)
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

        objetivo_limpio  = objetivo.replace(" ", "")
        respuesta_limpia = respuesta.replace(" ", "")
        total = len(objetivo_limpio)

        correctos_texto = sum(1 for a, b in zip(objetivo_limpio, respuesta_limpia) if a == b) #Combinar ambas frases y comparar las letras

        morse_esperado = [MORSE_INV.get(ch, "") for ch in objetivo.replace(" ", "")]
        correctos_morse = sum(1 for a, b in zip(morse_esperado, self.morse_ingresado) if a == b)
        precision = correctos_morse / total if total > 0 else 0

        puntaje_ronda = round(correctos_texto + (correctos_texto * precision)) #Cada letra correcta vale 1 punto, más un bonus por la precisión del Morse

        if self.fase == 1 and self.turno == "A":
            self.puntaje_a += puntaje_ronda
            self.label_resultado.config(text=f"Jugador A: {respuesta}  →  {correctos_texto}/{total} letras  |  precisión Morse: {round(precision*100)}%  |  puntaje: {puntaje_ronda}")
            self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
            self.cambiar_turno()
        elif self.fase == 1 and self.turno == "B":
            self.puntaje_b += puntaje_ronda
            self.label_resultado.config(text=f"Jugador B: {respuesta}  →  {correctos_texto}/{total} letras  |  precisión Morse: {round(precision*100)}%  |  puntaje: {puntaje_ronda}")
            self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
            self.cambiar_fase()
        elif self.fase == 2 and self.turno == "B":
            self.puntaje_b += puntaje_ronda
            self.label_resultado.config(text=f"Jugador B: {respuesta}  →  {correctos_texto}/{total} letras  |  precisión Morse: {round(precision*100)}%  |  puntaje: {puntaje_ronda}")
            self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
            self.cambiar_turno()
        elif self.fase == 2 and self.turno == "A":
            self.puntaje_a += puntaje_ronda
            self.label_resultado.config(text=f"Jugador A: {respuesta}  →  {correctos_texto}/{total} letras  |  precisión Morse: {round(precision*100)}%  |  puntaje: {puntaje_ronda}")
            self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
            if self.ronda_actual >= TOTAL_RONDAS:
                self.app.mostrar_final(self.puntaje_a, self.puntaje_b)
            else:
                self.mostrar_ganador()

    def add_space(self):
        if self.text and self.text[-1] != " ":
            self.text.append(" ")
            self.label_text.config(text="".join(self.text)) 

    def update_morse(self):
        self.label_morse.config(text="".join(self.buffer))

    def nueva_ronda(self):
        self.ronda_actual += 1
        self.fase = 1
        self.ronda_curso = False
        self.label_ronda.config(text=f"Ronda {self.ronda_actual}/{TOTAL_RONDAS}")
        self.frase_objetivo = random.choice(self.app.frases)
        self.label_objetivo.config(text=f"Escriba en Morse: {self.frase_objetivo}")
        self.text = []
        self.buffer = []
        self.morse_ingresado = []
        self.label_morse.config(text="")
        self.label_text.config(text="")
        self.label_resultado.config(text="")
        self.label_turno.config(text="Turno: Jugador A (teclado)")
        self.btn_nueva.config(state=tk.DISABLED)
        self.btn_randomizar.config(state=tk.NORMAL)
        self.btn_enviar.config(state=tk.NORMAL)
        self.turno = "A"
        self.label_turno.config(text="Turno: Jugador A (teclado) — Fase 1")
        self.bloquear_input()
        if self.timer:
            self.app.root.after_cancel(self.timer)
        if hasattr(self, "word_timer") and self.word_timer:
            self.app.root.after_cancel(self.word_timer)

    def cambiar_turno(self):
        self.text = []
        self.buffer = []
        self.morse_ingresado = []
        self.label_morse.config(text="")
        self.label_text.config(text="")

        if self.fase == 1:
            self.turno = "B"
            self.label_turno.config(text="Turno: Jugador B (maqueta) — Fase 1")
            self.bloquear_input()
        else:
            self.turno = "A"
            self.label_turno.config(text="Turno: Jugador A (maqueta) — Fase 2")
            self.bloquear_input()

    def mostrar_ganador(self):
        if self.puntaje_a > self.puntaje_b:
            ganador = "¡Va ganando el Jugador A!"
        elif self.puntaje_b > self.puntaje_a:
            ganador = "¡Va ganando el Jugador B!"
        else:
            ganador = "¡Van empate!"
        self.label_resultado.config(text=f"{ganador}  —  A: {self.puntaje_a} | B: {self.puntaje_b} - Ronda {self.ronda_actual}/{TOTAL_RONDAS}")
        self.turno = "A"
        self.fase = 1
        self.bloquear_input()
        self.btn_nueva.config(state=tk.NORMAL)
        self.btn_randomizar.config(state=tk.DISABLED)

    def cambiar_fase(self):
        self.fase = 2
        self.text = []
        self.buffer = []
        self.morse_ingresado = []
        self.label_morse.config(text="")
        self.label_text.config(text="")
        self.turno = "B"
        self.label_turno.config(text="Turno: Jugador B (teclado) — Fase 2")
        self.label_resultado.config(text="— Fase 2: ahora B usa el teclado y A la maqueta —")
        self.desbloquear_input()

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
        jugador_maqueta = "B" if self.fase == 1 else "A"
        if self.turno != jugador_maqueta:
            return
        self.buffer.append(simbolo)
        self.update_morse()
        self.reset_timer()

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

#Clase para la patalla de los resultados
class PantallaFinal(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        tk.Label(self, text="JUEGO TERMINADO", fg="red").pack(pady=30)

        self.label_puntaje_a = tk.Label(self, text="")
        self.label_puntaje_a.pack(pady=5)

        self.label_puntaje_b = tk.Label(self, text="")
        self.label_puntaje_b.pack(pady=5)

        self.label_ganador = tk.Label(self, text="")
        self.label_ganador.pack(pady=20)

        tk.Button(self, text="Jugar de nuevo", width=20,command=self.app.iniciar_juego).pack(pady=10)

        tk.Button(self, text="Menú principal", width=20, command=self.app.volver_inicio).pack(pady=5)

    def mostrar_resultados(self, puntaje_a, puntaje_b):
        self.label_puntaje_a.config(text=f"Jugador A: {puntaje_a} puntos")
        self.label_puntaje_b.config(text=f"Jugador B: {puntaje_b} puntos")

        if puntaje_a > puntaje_b:
            self.label_ganador.config(text="¡Ganó el Jugador A!")
        elif puntaje_b > puntaje_a:
            self.label_ganador.config(text="¡Ganó el Jugador B!")
        else:
            self.label_ganador.config(text="¡Empate!")

#Clase principal de la aplicación
class MorseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("StrangerTEC - Morse")
        self.root.geometry("500x500")

        self.frases = FRASES[:]  #Copia de la lista original para modificarla sin afectar la constante
        self.presentacion = "ambos"

        self.pantalla_inicio = PantallaInicio(root, self)
        self.pantalla_juego  = PantallaJuego(root, self)
        self.pantalla_final  = PantallaFinal(root, self)

        self.mostrar(self.pantalla_inicio)

    def mostrar(self, pantalla):
        self.pantalla_inicio.pack_forget()
        self.pantalla_juego.pack_forget()
        self.pantalla_final.pack_forget()
        pantalla.pack(fill=tk.BOTH, expand=True)

    def iniciar_juego(self):
        self.mostrar(self.pantalla_juego)
        self.pantalla_juego.iniciar()

    def volver_inicio(self):
        self.mostrar(self.pantalla_inicio)

    def mostrar_final(self, puntaje_a, puntaje_b):
        self.pantalla_final.mostrar_resultados(puntaje_a, puntaje_b)
        self.mostrar(self.pantalla_final)

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