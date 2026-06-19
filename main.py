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

from machine import Pin, PWM
import utime
import sys
import select
import network
import socket

#Pines
BUTTON_PIN = 16
BUZZER_PIN = 5
DIPSWITCH_PIN = 17

DATA_PIN  = 27
CLOCK_PIN = 26

FILA_1_PIN = 15  # A C E G I K M O Q S U W Y
FILA_2_PIN = 14  # B D F H J L N P R T V X Z
FILA_3_PIN = 13  # 0 1 2 3 4 5 6 7 8 9 - +

#circuito incrementador
BIT3_PIN = 22   # MSB
BIT2_PIN = 21
BIT1_PIN = 20
BIT0_PIN = 19   # LSB

#Tiempo base morse
UNIT_TIME = 250

#Configurar elementos de la maqueta
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
buzzer = PWM(Pin(BUZZER_PIN))
dipswitch = Pin(DIPSWITCH_PIN, Pin.IN, Pin.PULL_UP)
data = Pin(DATA_PIN,  Pin.OUT)
clock = Pin(CLOCK_PIN, Pin.OUT)
fila1 = Pin(FILA_1_PIN, Pin.OUT)
fila2 = Pin(FILA_2_PIN, Pin.OUT)
fila3 = Pin(FILA_3_PIN, Pin.OUT)

bit3 = Pin(BIT3_PIN, Pin.OUT)
bit2 = Pin(BIT2_PIN, Pin.OUT)
bit1 = Pin(BIT1_PIN, Pin.OUT)
bit0 = Pin(BIT0_PIN, Pin.OUT)

MORSE = {
    "A":'.-', "B":"-...", "C":"-.-.", "D":"-..",
    "E":".", "F":"..-.", "G":"--.", "H":"....",
    "I":"..", "J":".---", "K":"-.-", "L":".-..",
    "M":"--", "N":"-.", "O":"---", "P":".--.",
    "Q":"--.-", "R":".-.", "S":"...", "T":"-",
    "U":"..-", "V":"...-", "W":".--",  "X":"-..-",
    "Y":"-.--", "Z":"--..", "0":"-----","1":'.----',
    "2":"..---", "3":"...--", "4":"....-", "5":".....",
    "6":"-....", "7":"--...", "8":"---..","9":"----.",
    "+":'.-.-.', "-":"-....-"
}

#Orden de cada fila de leds
ORDEN_LED_1 = list("ACEGIKMOQSUWY")
ORDEN_LED_2 = list("BDFHJLNPRTVXZ")
ORDEN_LED_3 = list("0123456789-+")

#Fila de leds
FILA_1 = set("ACEGIKMOQSUWY")
FILA_2 = set("BDFHJLNPRTVXZ")
FILA_3 = set("0123456789-+")

#Conectar WiFi
SSID = "DJSA912"
PASSWORD = "AslanJavier"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)

print("Conectando a WiFi...")
timeout = 15   # segundos máximo de espera
while not wifi.isconnected() and timeout > 0:
    utime.sleep(1)
    timeout -= 1

if wifi.isconnected():
    print("WiFi conectado:", wifi.ifconfig())
else:
    print("WiFi no disponible — modo serial USB")

#Funcion para leer serial
def leer_serial():
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.readline().strip()
    return None

#Función para generar un pulso de reloj
def pulse_clock():
    clock.value(1) #Activa
    utime.sleep_us(2)
    clock.value(0) #Desactiva
    utime.sleep_us(2)

#Función para enviar los bits al registro de corrimiento
def send_bits(bits):
    for bit in reversed(bits): #Envia los bits en reverso para que tengan el orden adecuado
        data.value(1 if bit else 0) #Envia el 1 o 0
        pulse_clock() #Genera el pulso de reloj

#Apaga todos los leds
def leds_off():
    fila1.value(0)
    fila2.value(0)
    fila3.value(0)
    send_bits([False] * 16)

#Función para encender el LED correspondiente al caracter
def encender_led(char):
    char = char.upper()
    bits = [False] * 16
    #Busca el indice del caracter y lo activa
    if char in ORDEN_LED_1:
        bits[ORDEN_LED_1.index(char)] = True
    elif char in ORDEN_LED_2:
        bits[ORDEN_LED_2.index(char)] = True
    elif char in ORDEN_LED_3:
        bits[ORDEN_LED_3.index(char)] = True

    leds_off() #Apaga los anteriores
    send_bits(bits) #Enciende el nuevo led

    #Activa la fila correspondiente
    if char in FILA_1:
        fila1.value(1)
    elif char in FILA_2:
        fila2.value(1)
    elif char in FILA_3:
        fila3.value(1)

#Enciende buzzer
def buzzer_on():
    buzzer.freq(600)
    buzzer.duty_u16(32768) #Controlar volumen

#Apaga buzzer
def buzzer_off():
    buzzer.duty_u16(0)

#Envia un mensaje
def enviar_mensaje(mensaje):
    if cliente:
        try:
            cliente.send((mensaje + "\n").encode())
        except:
            pass
    else:
        print(mensaje)

#Circuito incrementador
def test_incrementador(binario):
    print(binario)
    bit3.value(int(binario[0]))
    bit2.value(int(binario[1]))
    bit1.value(int(binario[2]))
    bit0.value(int(binario[3]))

    utime.sleep_ms(50)

    entrada = int(binario, 2)
    
    resultado = entrada + 5

    resultado_bin = "{:04b}".format(resultado & 0x0F)

    print(f"TEST_RESULT: Entrada={binario} -> Salida={resultado_bin}")
    enviar_mensaje(f"TEST_RESULT:{binario}:{resultado_bin}")
        
def procesar_incrementador(letra):
    ascii_val = ord(letra.upper())
    entrada = ascii_val & 0x0F   # 4 bits menos significativos

    binario = format(entrada, "04b")

    bit3.value(int(binario[0]))
    bit2.value(int(binario[1]))
    bit1.value(int(binario[2]))
    bit0.value(int(binario[3]))

    resultado = entrada + 5
    salida_bin = "{:04b}".format(resultado & 0x0F)

    enviar_mensaje(f"INCR:{letra}:{ascii_val}:{entrada}:{salida_bin}")

#Función para reproducir una frase
def reproducir_frase(frase, modo):
    #Definir el tiempo de morse
    PUNTO = UNIT_TIME
    RAYA  = UNIT_TIME * 3
    GAP_SIMBOLO  = UNIT_TIME
    GAP_CARACTER = UNIT_TIME * 3
    GAP_PALABRA  = UNIT_TIME * 7

    #Recorre cada caracter de la frase
    for i, ch in enumerate(frase.upper()):
        if ch == ' ': #Si es un espacio espera el tiempo de espacio
            leds_off()
            utime.sleep_ms(GAP_PALABRA)
            continue
        if ch not in MORSE: #Si no existe en morse lo ignora
            continue

        codigo = MORSE[ch]

        #Recorre cada simbolo morse del código
        for j, simbolo in enumerate(codigo):
            duracion = PUNTO if simbolo == '.' else RAYA
            
            #Si el modo lo permite activa elbuzzer, leds oambos
            if modo in ("sonido", "ambos"):
                buzzer_on()

            if modo in ("leds", "ambos"):
                encender_led(ch)

            utime.sleep_ms(duracion)

            buzzer_off()

            if modo == "leds":
                utime.sleep_ms(duracion // 2)
            leds_off()

            #Espera entre simblos
            if j < (len(codigo) - 1):
                utime.sleep_ms(GAP_SIMBOLO)

        #Espera entre caracteres 
        if i < (len(frase) - 1) and frase[i + 1] != ' ':
            utime.sleep_ms(GAP_CARACTER)

#Recepcion de mensajes
def procesar_comando(datos):
    if datos.startswith("FRASE:"):
        partes = datos[6:].split(":")
        frase = partes[0]
        modo = partes[1] if len(partes) > 1 else "ambos"
        reproducir_frase(frase, modo)

    elif datos.startswith("TEST:"):
        binario = datos[5:].strip()
        if len(binario) == 4:
            test_incrementador(binario)

    elif datos.startswith("LETRA:"):
        letra = datos[6:].strip()
        if len(letra) == 1:
            procesar_incrementador(letra)

#Servidor
print("Creando servidor...")
addr = socket.getaddrinfo("0.0.0.0", 1234)[0][-1]
server = socket.socket()
server.bind(addr)
server.listen(1)

print("Esperando conexión...")
cliente = None

if wifi.isconnected():
    print("Esperando conexión WiFi...")
    inicio = utime.time()
    while cliente is None and (utime.time() - inicio) < 10:
        try:
            cliente, direccion = server.accept()
            cliente.settimeout(0.1)
            print("Cliente conectado:", direccion)
        except:
            utime.sleep_ms(100)
if cliente is None:
    print("Modo USB")

for i in range(3):
    buzzer_on()
    utime.sleep_ms(200)
    buzzer_off()
    utime.sleep_ms(200)

#Lee el estado del dipswitch inicial
modo_juego = "simple" if dipswitch.value() == 0 else "escucha"
print(f"MODO:{modo_juego}")

while True:
    #Revisa si cambió el estado del dipswitch
    nuevo_modo = "simple" if dipswitch.value() == 0 else "escucha"
    if nuevo_modo != modo_juego:
        modo_juego = nuevo_modo
        enviar_mensaje(f"MODO:{modo_juego}")

    #Revisa si llegaron datos de la pc
    # Mensajes por WiFi
    if cliente:
        try:
            datos = cliente.recv(1024).decode()
            
            for linea in datos.splitlines():
                procesar_comando(linea.strip())
        except:
            pass

    # Mensajes por USB
    try:
        datos = leer_serial()

        if datos:
            procesar_comando(datos)
    except:
        pass

    if button.value() == 0: #Si el botón fue presionado
        press_start = utime.ticks_ms() 
        buzzer_on()
        while button.value() == 0: #Espera meintras el otón esta presionado
            utime.sleep_ms(10)
        buzzer_off()
        duration = utime.ticks_diff(utime.ticks_ms(), press_start) #Tiempo cuando dejo de ser presionado - tiempo cuando fue presionado
        if duration < UNIT_TIME * 2: #Presión corta
            enviar_mensaje("DOT")
        else: #Presion larga
            enviar_mensaje("DASH")