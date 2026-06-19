"""
Instituto Tecnológico de Costa Rica
Escuela de Ingeniería en Computadores
Fundamentos de sistemas computacionales - CE 1104
2026
Version del juego: 1.1
Python 3.12.4
EstudianteS: Samuel Ugalde Abrahams - 2026006212 y Jacky Yin Lu - 2026006278
Proyecto StrangerTEC - Morse
Descripción: Juego en el que compiten dos jugadores y se pone a
prueba su capacidad para enviar y recibir mensajes en código Morse utilizando
distintos medios (luces o sonido)
"""

import tkinter as tk
import time
import random
import threading
import serial
import serial.tools.list_ports
import socket

FRASES = ["SOS", "SI", "NO", "HOLA", "TEC", "MORSE", "WILL", "UPSIDE DOWN", "STRANGER", "JOYCE"]

# Diccionario morse a alfabeto
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

# Diccionario alfabeto a morse
MORSE_INV = {v: k for k, v in MORSE.items()}

CARACTERES_VALIDOS = set(MORSE_INV.keys()) | {" "}

#Rondas de juego
TOTAL_RONDAS = 3

#Words per minute
WPM_LENTO  = 5
WPM_MEDIO  = 8

#Clase para la pantalla de inicio
class PantallaInicio(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent) #trae todas las funcionalidades de tk.Frame
        self.app = app

        tk.Label(self, text="StrangerTEC", fg="red").pack(pady=30)
        tk.Label(self, text="Morse Translator", fg="gray").pack()

        tk.Label(self, text="Modo de presentación:").pack(pady=(15, 0))
        self.modo_var = tk.StringVar(value="ambos")

        #Botones para seleccionar el modo de presentación (luces, sonido o ambos)
        tk.Radiobutton(self, text="Solo luces (LEDs)", variable=self.modo_var, value="leds").pack()
        tk.Radiobutton(self, text="Solo sonido (buzzer)", variable=self.modo_var, value="sonido").pack()
        tk.Radiobutton(self, text="Luces y sonido", variable=self.modo_var, value="ambos").pack()

        self.label_modo_actual = tk.Label(self, text="Modo de juego: Escucha y Transmisión", fg="blue")
        self.label_modo_actual.pack(pady=(10, 0))

        tk.Button(self, text="Iniciar juego", width=20, bg="green", fg="white", command=self.iniciar).pack(pady=20) #Botón para iniciar el juego

        tk.Button(self, text="Editar frases", width=20, bg="orange", fg="white", command=self.app.editor_frases).pack(pady=5) #Botón para editar las frases del juego

        tk.Button(self, text="Probar incrementador", width=20, bg="blue", fg="white", command=self.app.ventana_incrementador).pack(pady=20) #Boton para probar el incrementador

    #Inicia el juego
    def iniciar(self):
        self.app.presentacion = self.modo_var.get()
        self.app.iniciar_juego()

#Clase para la GUI del juego
class PantallaJuego(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        #Atributos para el juego
        self.press_time = None
        self.is_pressed = False
        self.unit_time = 0.25 #Tiempo base para morse
        self.buffer = [] #Buffer para almacenar los símbolos Morse ingresados antes de decodificar a letra
        self.text = [] #Texto ingresado por el jugador
        self.morse_ingresado = []
        self.timer = None
        self.word_timer = None
        self.puntaje = 0
        self.serial_port = None
        self.puntaje_a = 0
        self.puntaje_b = 0
        self.turno = "A"
        self.ronda_actual = 0
        self.fase = 1
        self.ronda_curso = False

        #GUI
        self.label_modo = tk.Label(self, text="Modo: Escucha y Transmisión", fg="blue")
        self.label_modo.pack()

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

        #Resultado incrementador
        self.label_incr = tk.Label(self, text="")
        self.label_incr.pack()

        #Botones
        frame_botones = tk.Frame(self)
        frame_botones.pack(pady=10)

        self.btn_randomizar = tk.Button(frame_botones, text="Randomizar frase",command=self.randomizar_frase) #Botón para randomizar la frase objetivo
        self.btn_randomizar.pack(side=tk.LEFT, padx=5)

        self.btn_enviar = tk.Button(frame_botones, text="Enviar frase", command=self.enviar_frase, state=tk.DISABLED) #Botón para enviar la frase a la maqueta, solo habilitado en modo escucha y transmisión
        self.btn_enviar.pack(side=tk.LEFT, padx=5)

        self.btn_nueva = tk.Button(frame_botones, text="Nueva ronda", command=self.nueva_ronda, state=tk.DISABLED) #Botón para iniciar una nueva ronda, solo habilitado después de evaluar la ronda actual
        self.btn_nueva.pack(side=tk.LEFT, padx=5)

        self.volver_menu = tk.Button(frame_botones, text="Menú principal", command=self.app.volver_inicio) #Botón para volver al menú principal
        self.volver_menu.pack(side=tk.LEFT, padx=5)

    #Función para reproducir la frase en la maqueta
    def iniciar(self):
        #Reiniciar variables y estado del juego
        self.puntaje_a = 0
        self.puntaje_b = 0
        self.ronda_actual = 0
        self.turno = "A"
        self.fase = 1
        self.ronda_curso = False
        self.tiempo_inicio = None
        self.modo_juego = self.app.modo_juego
        texto_modo = "Modo: Transmisión Simple" if self.modo_juego == "simple" else "Modo: Escucha y Transmisión"
        self.label_modo.config(text=texto_modo)
        self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
        self.label_turno.config(text="Turno: Jugador A (teclado)")
        self.label_resultado.config(text="")

        self.bloquear_input() #Deshabilitar el ingreso de Morse por teclado hasta que se inicie la ronda
        self.nueva_ronda() #Iniciar la primera ronda
        self.conectar_serial() #Conectar con la maqueta al iniciar el juego

    #Función cuando se presiona el botón para registrar el tiempo en el que se presionó
    def key_press(self, event):
        jugador_teclado = "A" if self.fase == 1 else "B"
        if self.turno != jugador_teclado:
            return
        if self.is_pressed:
            return
        self.is_pressed = True
        self.press_time = time.time()

    #Función cuando se suelta el botón
    def key_release(self, event):
        jugador_teclado = "A" if self.fase == 1 else "B"
        if self.turno != jugador_teclado:
            return
        if not self.is_pressed:
            return

        duration = time.time() - self.press_time #Calcular la duración de la pulsación

        if duration < self.unit_time: #Si la duración es menor al tiempo base, se considera un punto, de lo contrario una raya
            symbol = "."
        else:
            symbol = "-"

        self.buffer.append(symbol)
        self.update_morse()
        self.reset_timer()

        self.press_time = None
        self.is_pressed = False

    #Función para bloquear el ingreso de Morse por teclado
    def bloquear_input(self):
        self.app.root.unbind("<KeyPress-space>")
        self.app.root.unbind("<KeyRelease-space>")

    #Función para desbloquear el ingreso de Morse por teclado
    def desbloquear_input(self):
        self.app.root.bind("<KeyPress-space>", self.key_press)
        self.app.root.bind("<KeyRelease-space>", self.key_release)

    #Función para randomizar la frase objetivo de la ronda
    def randomizar_frase(self):
        if not self.ronda_curso:
            self.frase_objetivo = random.choice(self.app.frases) #Selecciona una frase random 
            self.label_objetivo.config(text=f"Escriba en Morse: {self.frase_objetivo}")

    #Función para enviar la frase objetivo y el modo de presentación a la maqueta a través del puerto serial
    def enviar_frase(self):
        modo = self.app.presentacion
        mensaje = f"FRASE:{self.frase_objetivo}:{modo}\n"
        self.app.enviar_datos(mensaje) #Enviar la frase y el modo a la maqueta
        self.btn_randomizar.config(state=tk.DISABLED)
        self.btn_enviar.config(state=tk.DISABLED)
        self.ronda_curso = True
        if self.modo_juego != "simple":
            self.desbloquear_input()

    #Función para reiniciar los timers de decodificación de letra y espacio entre palabras
    def reset_timer(self):
        if self.timer:
            self.app.root.after_cancel(self.timer)

        self.timer = self.app.root.after(int(4 * self.unit_time * 1000), self.decode_letter)
        self.word_timer = self.app.root.after(int(8 * self.unit_time * 1000), self.add_space)

    #Función para decodificar el código Morse ingresado a letra
    def decode_letter(self):
        code = "".join(self.buffer) #Unir los símbolos morse ingresados
        char = MORSE.get(code, "?") #Decodificar el código morse a letra
        self.morse_ingresado.append(code) #Guardar el código morse ingresado
        self.text.append(char) #Agregar la letra decodificada al texto ingresado
        self.label_text.config(text="".join(self.text))

        self.buffer = []
        self.label_morse.config(text="")

        if char != "?": #Enviar character a la pico para el incrementador
            self.app.enviar_datos(f"LETRA:{char}\n")

        if hasattr(self, "word_timer") and self.word_timer: #Revisa si tiene el atributo word_timer y si existe un timer activo
            self.app.root.after_cancel(self.word_timer) #Cancelar el timer de espacio entre palabras
            self.word_timer = None #Reiniciar el timer de espacio entre palabras

        texto_actual = "".join(self.text).strip() #Texto ingresado hasta el momento sin espacios
        if len(texto_actual.replace(" ", "")) >= len(self.frase_objetivo.replace(" ", "")): #Si el texto ingresado tiene al menos la misma cantidad de caracteres que la frase objetivo, se evalúa la respuesta
            self.evaluar()

    #Función para evaluar la respuesta del jugador,
    def evaluar(self):
        respuesta = "".join(self.text).strip().upper() #Respuesta ingresada por el jugador convertida a mayúsculas y sin espacios al inicio o final
        objetivo  = self.frase_objetivo.upper() 

        objetivo_limpio  = objetivo.replace(" ", "")
        respuesta_limpia = respuesta.replace(" ", "")
        total = len(objetivo_limpio) #Cantidad de caracteres en la frase objetivo sin espacios

        correctos_texto = sum(1 for a, b in zip(objetivo_limpio, respuesta_limpia) if a == b) #Combinar ambas frases y comparar las letras, suma 1 si son iguales

        if self.modo_juego == "simple": #Puntaje por velocidad
            multiplicador, nivel_wpm = self.calcular_wpm() #Calcula multiplicador y velocidad 
            puntaje_ronda = round(correctos_texto * multiplicador) #Cada letra correcta vale 1 punto, multiplicado por el nivel de velocidad
            detalle = f"velocidad: {nivel_wpm}"
        else: #Puntaje por precisión
            morse_esperado = [MORSE_INV.get(ch, "") for ch in objetivo.replace(" ", "")] #Lista con el código morse esperado para cada letra de la frase objetivo
            correctos_morse = sum(1 for a, b in zip(morse_esperado, self.morse_ingresado) if a == b) #Combinar el código morse esperado con el ingresado y comparar, suma 1 por cada código morse correcto
            precision = correctos_morse / total if total > 0 else 0 #Calcular precisión como cantidad de códigos morse correctos sobre el total de caracteres
            puntaje_ronda = round(correctos_texto + (correctos_texto * precision)) #Cada letra correcta vale 1 punto, más un bonus por la precisión del Morse
            detalle = f"precisión Morse: {round(precision*100)}%"

        if self.modo_juego == "simple": #Modo transmision simple
            if self.turno == "A":
                #Actualiza atributos y etiquetas
                self.puntaje_a += puntaje_ronda
                self.label_resultado.config(text=f"Jugador A: {respuesta}  →  {correctos_texto}/{total} letras  |  {detalle}  |  puntaje: {puntaje_ronda}")
                self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
                self.text = []
                self.buffer = []
                self.morse_ingresado = []
                self.tiempo_inicio = None
                self.label_morse.config(text="")
                self.label_text.config(text="")
                self.turno = "B"
                self.label_turno.config(text="Turno: Jugador B (maqueta) — transmitir")
            else: #Turno de B
                #Actualiza atributos y etiquetas
                self.puntaje_b += puntaje_ronda
                self.label_resultado.config(text=f"Jugador B: {respuesta}  →  {correctos_texto}/{total} letras  |  {detalle}  |  puntaje: {puntaje_ronda}")
                self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
                if self.ronda_actual >= TOTAL_RONDAS: #Si se han jugado todas las rondas se muestra pantalla con resultados
                    self.app.mostrar_final(self.puntaje_a, self.puntaje_b)
                else: #Mostrar ganador de la ronda y botón para nueva ronda
                    self.mostrar_ganador()
        else: #Modo escucha y transmision
            if self.fase == 1 and self.turno == "A": #Fase 1: A ingresó Morse teclado
                self.puntaje_a += puntaje_ronda
                self.label_resultado.config(text=f"Jugador A: {respuesta}  →  {correctos_texto}/{total} letras  |  {detalle}  |  puntaje: {puntaje_ronda}")
                self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
                self.cambiar_turno()
            elif self.fase == 1 and self.turno == "B": #Fase 1: B ingresó Morse maqueta
                self.puntaje_b += puntaje_ronda
                self.label_resultado.config(text=f"Jugador B: {respuesta}  →  {correctos_texto}/{total} letras  |  {detalle}  |  puntaje: {puntaje_ronda}")
                self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
                self.cambiar_fase()
            elif self.fase == 2 and self.turno == "B": #Fase 2: B ingresó Morse teclado
                self.puntaje_b += puntaje_ronda
                self.label_resultado.config(text=f"Jugador B: {respuesta}  →  {correctos_texto}/{total} letras  |  {detalle}  |  puntaje: {puntaje_ronda}")
                self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
                self.cambiar_turno()
            elif self.fase == 2 and self.turno == "A": #Fase 2: A ingresó Morse maqueta
                self.puntaje_a += puntaje_ronda
                self.label_resultado.config(text=f"Jugador A: {respuesta}  →  {correctos_texto}/{total} letras  |  {detalle}  |  puntaje: {puntaje_ronda}")
                self.label_puntaje.config(text=f"Jugador A: {self.puntaje_a}  |  Jugador B: {self.puntaje_b}")
                if self.ronda_actual >= TOTAL_RONDAS: #Si ya pasaron todas las rondas se muestran los resultados
                    self.app.mostrar_final(self.puntaje_a, self.puntaje_b)
                else: #Mostrar ganador de la ronda y botón para nueva ronda
                    self.mostrar_ganador()

    #Función para agregar espacio despues de que haya pasado el word_timer
    def add_space(self):
        if self.text and self.text[-1] != " ": #Si existe texto y no hay un espacio en la última posicion pone el espacio
            self.text.append(" ")
            self.label_text.config(text="".join(self.text)) 

    #Actualiza la etiqueta que muestra el código Morse ingresado
    def update_morse(self):
        self.label_morse.config(text="".join(self.buffer))

    #Funcion para iniciar una nueva ronda
    def nueva_ronda(self):
        #Actualiza atributos, labels y botones
        self.ronda_actual += 1
        self.fase = 1
        self.tiempo_inicio = None
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
        self.btn_nueva.config(state=tk.DISABLED) 
        self.btn_randomizar.config(state=tk.NORMAL)
        self.turno = "A"

        if self.modo_juego == "simple":
            self.label_turno.config(text="Turno: Jugador A (maqueta) — transmitir")
            self.btn_enviar.config(state=tk.DISABLED)
        else:
            self.label_turno.config(text="Turno: Jugador A (teclado) — Fase 1")
            self.btn_enviar.config(state=tk.NORMAL)

        self.bloquear_input()
        if self.timer: #Si hay timer lo cancela
            self.app.root.after_cancel(self.timer)
        if hasattr(self, "word_timer") and self.word_timer: #Si hay word_timer lo cancela
            self.app.root.after_cancel(self.word_timer)

    #Funcion para cambiar turno en modo escucha
    def cambiar_turno(self):
        #Actualiza atributos y labels
        self.text = []
        self.buffer = []
        self.morse_ingresado = []
        self.label_morse.config(text="")
        self.label_text.config(text="")

        if self.fase == 1: #El turno pasa al Jugador B usando la maqueta
            self.turno = "B"
            self.label_turno.config(text="Turno: Jugador B (maqueta) — Fase 1")
            self.bloquear_input()
        else: #El turno pasa al Jugador A usando la maqueta
            self.turno = "A"
            self.label_turno.config(text="Turno: Jugador A (maqueta) — Fase 2")
            self.bloquear_input()

    #Función para mostrar el ganador de la ronda y actualizar el estado del juego
    def mostrar_ganador(self):
        #Mostrar ganador de la ronda
        if self.puntaje_a > self.puntaje_b:
            ganador = "¡Va ganando el Jugador A!"
        elif self.puntaje_b > self.puntaje_a:
            ganador = "¡Va ganando el Jugador B!"
        else:
            ganador = "¡Van empate!"
        #Actualizar etiquetas y atributos
        self.label_resultado.config(text=f"{ganador}  —  A: {self.puntaje_a} | B: {self.puntaje_b} - Ronda {self.ronda_actual}/{TOTAL_RONDAS}")
        self.turno = "A"
        self.fase = 1
        self.bloquear_input() #Deshabilitar ingreso de Morse por teclado mientras se muestra el resultado
        self.btn_nueva.config(state=tk.NORMAL) #Habilitar el botón de nueva ronda
        self.btn_randomizar.config(state=tk.DISABLED) #Deshabilitar el botón de randomizar

    #Función para cambiar de fase
    def cambiar_fase(self):
        #Actualizar atributos y labels, turno pasa a jugador B en teclado
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

    #Función para conectar con la maqueta
    def conectar_serial(self):
        if self.app.serial_port and self.app.serial_port.is_open: #Si ya existe la conneción, actualiza atributos
            self.serial_port = self.app.serial_port
            self.label_serial.config(text=f"Maqueta: conectada", fg="green")
            return
        #Conecta a maqueta
        puertos = serial.tools.list_ports.comports()
        for p in puertos:
            if "USB" in p.description or "Pico" in p.description:
                try:
                    self.serial_port = serial.Serial(p.device, 115200, timeout=1)
                    self.app.serial_port = self.serial_port
                    self.label_serial.config(text=f"Maqueta: conectada ({p.device})", fg="green")
                    return
                except Exception:
                    pass
        if not self.app.conectar_wifi:
            self.label_serial.config(text="Maqueta: no encontrada — solo teclado", fg="red") #No se logro conectar
        self.label_serial.config(text=f"Maqueta: conectada por WiFi", fg="green")

    #Funcion para recibir un simbolo morse enviado desde la maqueta
    def recibir_simbolo(self, simbolo: str):
        if self.modo_juego == "simple": #En modo simple da igual que jugador es
            pass
        else: #Verifica que sea el turno del jugador que esta en la maqueta
            jugador_maqueta = "B" if self.fase == 1 else "A"
            if self.turno != jugador_maqueta:
                return
        
        if self.modo_juego == "simple" and self.tiempo_inicio is None: #Inicia cronometro al recibir el primer simbolo
            self.tiempo_inicio = time.time()
            self.ronda_curso = True
            self.btn_randomizar.config(state=tk.DISABLED)

        self.buffer.append(simbolo)
        self.update_morse() #Actualiza morse
        self.reset_timer() #Actualiza timer

    #Función para calcular el WPM y determinar el nivel de velocidad del jugador
    def calcular_wpm(self):
        if not self.tiempo_inicio:
            return 1.0, "lento"
        transcurrido = time.time() - self.tiempo_inicio
        chars = len(self.frase_objetivo.replace(" ", "")) #Cantidad de caracteres en la frase objetivo sin espacios
        wpm = (chars / 5) / (transcurrido / 60) if transcurrido > 0 else 0 #Formula para calcular WPM
        if wpm >= WPM_MEDIO: #Si WPM es mayor o igual al umbral de medio se considera rápido
            return 2.0, f"rápido ({round(wpm, 1)} WPM)"
        elif wpm >= WPM_LENTO: #Si WPM es mayor o igual al umbral de lento pero menor al de medio se considera medio
            return 1.5, f"medio ({round(wpm, 1)} WPM)"
        else: #Si WPM es menor al umbral de lento se considera lento
            return 1.0, f"lento ({round(wpm, 1)} WPM)"
        
    #Mostrar incrementador
    def mostrar_incr(self, linea):
        partes = linea[5:].split(":")
        if len(partes) < 4:
            return
        letra = partes[0]
        ascii_val = partes[1]
        entrada = int(partes[2])
        salida_bin = partes[3].strip()
        entrada_bin = format(entrada, '04b') #Convertirlo a binario
        salida = int(salida_bin, 2)
        self.label_incr.config(text=f"Letra: {letra} | ASCII: {ascii_val} | "f"Entrada: {entrada_bin} ({entrada}) | Salida +5: {salida_bin} ({salida})")

#Clase para la patalla de los resultados
class PantallaFinal(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        #Atributos y labels
        self.app = app

        tk.Label(self, text="JUEGO TERMINADO", fg="red").pack(pady=30)

        self.label_puntaje_a = tk.Label(self, text="")
        self.label_puntaje_a.pack(pady=5)

        self.label_puntaje_b = tk.Label(self, text="")
        self.label_puntaje_b.pack(pady=5)

        self.label_ganador = tk.Label(self, text="")
        self.label_ganador.pack(pady=20)

        tk.Button(self, text="Jugar de nuevo", width=20,command=self.app.iniciar_juego).pack(pady=10) #Boton para volver a jugar

        tk.Button(self, text="Menú principal", width=20, command=self.app.volver_inicio).pack(pady=5) #Boton para volver al menu principal

    #Funcion para mostrar los resultados de la partida
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
        #Crear ventana
        self.root = root
        self.root.title("StrangerTEC - Morse")
        self.root.geometry("500x500")

        self.frases = FRASES[:]  #Copia de la lista original para modificarla sin afectar la constante
        self.presentacion = "ambos" #Modo de presentación
        self.modo_juego = "escucha" #Modo de juego
        self.serial_port = None
        self.socket_con = None
        self.modo_conexion = "serial"  # Coneecion por cable o wifi

        self.pantalla_inicio = PantallaInicio(root, self)
        self.pantalla_juego  = PantallaJuego(root, self)
        self.pantalla_final  = PantallaFinal(root, self)
        self.serial_port = None #Puerto serial

        self.mostrar(self.pantalla_inicio)
        if not self.conectar_serial(): #Intentar conectar al wifi si no se conecta al serial
            self.conectar_wifi()
        
        self.label_test_incrementador = None

    #Conecta con la maqueta usando serial
    def conectar_serial(self):
        puertos = serial.tools.list_ports.comports()
        for p in puertos:
            if "USB" in p.description or "Pico" in p.description:
                try:
                    self.serial_port = serial.Serial(p.device, 115200, timeout=1) #Abre la conección serial con maqueta
                    self.modo_conexion = "serial" #Actualizamo modo de conexion
                    hilo = threading.Thread(target=self.leer_serial, daemon=True) #Inicia un hilo para leer el puerto serial sin bloquear la interfaz
                    hilo.start()
                    return True
                except Exception:
                    pass
        return False

    #Leer los datos del puerto serial y actualizar la interfaz según el mensaje recibido
    def leer_serial(self):
        while self.serial_port and self.serial_port.is_open:
            try:
                linea = self.serial_port.readline().decode("utf-8").strip() #Lee una línea del puerto serial, decodifica y elimina espacios
                self.procesar_mensajes(linea) #Procesa el mensaje
            except Exception:
                break

    #Conectar usando wifi
    def conectar_wifi(self):
        try:
            host = "192.168.68.115"
            puerto = 1234
            self.socket_con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_con.connect((host, puerto))
            self.modo_conexion = "wifi"
            hilo = threading.Thread(target=self.leer_wifi, daemon=True)
            hilo.start()
            return True
        except Exception as e:
            return False

    #Leer mensajes wifi
    def leer_wifi(self):
        while True:
            try:
                linea = self.socket_con.recv(1024).decode() #Lee una linea del socket
                self.procesar_mensajes(linea) #Procesa el mensaje
            except:
                break

    #Función para mostrar una pantalla y ocultar las demás
    def mostrar(self, pantalla):
        self.pantalla_inicio.pack_forget()
        self.pantalla_juego.pack_forget()
        self.pantalla_final.pack_forget()
        pantalla.pack(fill=tk.BOTH, expand=True)

    #Enviar datos usando serial o wifi
    def enviar_datos(self, mensaje):
        try:
            if self.modo_conexion == "serial":
                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.write(mensaje.encode("utf-8"))

            elif self.modo_conexion == "wifi":
                if self.socket_con:
                    self.socket_con.send(mensaje.encode())

        except Exception as e:
            print("Error enviando:", e)

    #Procesar mensajes recibidos
    def procesar_mensajes(self, linea):
        linea = linea.strip()

        if linea.startswith("MODO:"): #Actualiza modo
            modo = linea[5:].strip()
            self.root.after(0, self.modo_dipswitch, modo)
        elif linea == "DOT": #Recibe un punto
            self.root.after(0, self.pantalla_juego.recibir_simbolo, ".")
        elif linea == "DASH": #Recibe raya
            self.root.after(0, self.pantalla_juego.recibir_simbolo, "-")
        elif linea.startswith("INCR:"): #Resultado del incrementador
            self.root.after(0, self.pantalla_juego.mostrar_incr, linea)
        elif linea.startswith("TEST_RESULT:"): #Resultado de la prueba del incrementador
            self.root.after(0, self.mostrar_test_incr, linea)

    #Actualizar el modo de juego segun el dipswitch
    def modo_dipswitch(self, modo):
        self.modo_juego = modo
        texto = "Transmisión Simple" if modo == "simple" else "Escucha y Transmisión"
        self.pantalla_inicio.label_modo_actual.config(text=f"Modo de juego: {texto}")

    #Iniciar el juego desde la pantalla de inicio
    def iniciar_juego(self):
        self.mostrar(self.pantalla_juego)
        self.pantalla_juego.iniciar()

    #Volver al menú principal desde el juego o la pantalla final
    def volver_inicio(self):
        self.mostrar(self.pantalla_inicio)

    #Mostrar la pantalla final con los resultados del juego
    def mostrar_final(self, puntaje_a, puntaje_b):
        self.pantalla_final.mostrar_resultados(puntaje_a, puntaje_b)
        self.mostrar(self.pantalla_final)

    #Función para editar las frases desde la pantalla de inicio
    def editor_frases(self):
        #Crear ventana para editar frases
        win = tk.Toplevel(self.root)
        win.title("Editar frases")
        win.geometry("350x420")
        win.resizable(False, False)

        tk.Label(win, text="Edite las frases (máx. 16 caracteres cada una)").pack(pady=5)

        #Función de validación para permitir solo caracteres válidos en Morse
        def solo_validos(new_text):
            return all(ch.upper() in CARACTERES_VALIDOS for ch in new_text)
        vcmd = win.register(solo_validos) #Registrar la función de validación

        entries = []
        for i, frase in enumerate(self.frases): #Crear un campo de texto para cada frase
            frame = tk.Frame(win)
            frame.pack(fill=tk.X, padx=15, pady=2)
            tk.Label(frame, text=f"{i+1}.", width=3).pack(side=tk.LEFT)
            var = tk.StringVar(value=frase) #Almacena el texto del campo
            tk.Entry(frame, textvariable=var, width=20, validate="key", validatecommand=(vcmd, "%P")).pack(side=tk.LEFT, padx=5) #Input con validación
            contador = tk.Label(frame, text=f"{len(frase)}/16", width=6, fg="green" if len(frase) <= 16 else "red") #Contador de caracteres
            contador.pack(side=tk.LEFT)
            #Función para actualizar el contador de caracteres
            def actualizar(var=var, contador=contador):
                largo = len(var.get())
                contador.config(text=f"{largo}/16", fg="green" if largo <= 16 else "red")
            var.trace_add("write", lambda *args, v=var, c=contador: actualizar(v, c)) #Cada vez que cambia el texto actualiza el contador
            entries.append(var) #Guárda la variable

        label_error = tk.Label(win, text="", fg="red")
        label_error.pack(pady=3)

        #Función para guardar las frases editadas
        def guardar():
            nuevas = []
            for i, var in enumerate(entries):
                texto = var.get().strip().upper()
                if len(texto) == 0: #Revisa que no haya frases vacías
                    label_error.config(text=f"La frase {i+1} está vacía.")
                    return
                if len(texto) > 16: #Revisa que no haya frases con más de 16 caracteres
                    label_error.config(text=f"La frase {i+1} supera los 16 caracteres.")
                    return
                nuevas.append(texto)
            self.frases = nuevas
            win.destroy()

        frame_btns = tk.Frame(win)
        frame_btns.pack(pady=10)
        tk.Button(frame_btns, text="Guardar", command=guardar, bg="green", fg="white", width=10).pack(side=tk.LEFT, padx=5) #Boton para guardar frases editadas
        tk.Button(frame_btns, text="Cancelar", command=win.destroy, bg="red", fg="white", width=10).pack(side=tk.LEFT, padx=5) #Boton para cancelar la edición

    def ventana_incrementador(self):
        win = tk.Toplevel(self.root)
        win.title("Test Incrementador")
        win.geometry("350x250")
        win.resizable(False, False)

        tk.Label(win, text="Ingrese un número binario de 4 bits").pack(pady=10)

        entrada = tk.StringVar()
        tk.Entry(win, textvariable=entrada, width=10).pack()

        resultado = tk.Label(win, text="")
        resultado.pack(pady=10)

        def probar():
            binario = entrada.get().strip()

            if len(binario) != 4 or any(c not in "01" for c in binario):
                resultado.config(text="Ingrese exactamente 4 bits", fg="red")
                return

            self.enviar_datos(f"TEST:{binario}")

        tk.Button(win,text="Probar", command=probar).pack(pady=10)

        self.label_test_incrementador = resultado

        def cerrar():
            self.label_test_incrementador = None
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", cerrar)

    #Mostrar prueba de incrementador
    def mostrar_test_incr(self, linea):
        if self.label_test_incrementador is None:
            return
        
        partes = linea[12:].split(":")  # quita TEST_RESULT:
        if len(partes) < 2:
            return
        
        entrada = partes[0]
        salida  = partes[1]
        self.label_test_incrementador.config(text=f"TEST — Entrada: {entrada} ({int(entrada,2)})  →  "f"Salida: {salida} ({int(salida,2)})")

#Correr la aplicación
root = tk.Tk()
app = MorseApp(root)
root.mainloop()