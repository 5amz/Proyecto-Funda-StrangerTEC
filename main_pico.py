from machine import Pin, PWM
import utime
import sys
import select

BUTTON_PIN = 16
BUZZER_PIN = 5

DATA_PIN  = 27
CLOCK_PIN = 26

FILA_1_PIN = 15  # A C E G I K M O Q S U W Y
FILA_2_PIN = 14  # B D F H J L N P R T V X Z
FILA_3_PIN = 13  # 0 1 2 3 4 5 6 7 8 9 - +

UNIT_TIME = 300

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
buzzer = PWM(Pin(BUZZER_PIN))
data = Pin(DATA_PIN,  Pin.OUT)
clock = Pin(CLOCK_PIN, Pin.OUT)
fila1 = Pin(FILA_1_PIN, Pin.OUT)
fila2 = Pin(FILA_2_PIN, Pin.OUT)
fila3 = Pin(FILA_3_PIN, Pin.OUT)

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

ORDEN_LED_1 = list("ACEGIKMOQSUWY")
ORDEN_LED_2 = list("BDFHJLNPRTVXZ")
ORDEN_LED_3 = list("0123456789-+")

FILA_1 = set("ACEGIKMOQSUWY")
FILA_2 = set("BDFHJLNPRTVXZ")
FILA_3 = set("0123456789-+")

def pulse_clock():
    clock.value(1)
    utime.sleep_us(2)
    clock.value(0)
    utime.sleep_us(2)

def send_bits(bits):
    for bit in reversed(bits):
        data.value(1 if bit else 0)
        pulse_clock()

def leds_off():
    fila1.value(0)
    fila2.value(0)
    fila3.value(0)
    send_bits([False] * 16)

def encender_led(char):
    char = char.upper()
    bits = [False] * 16
    if char in ORDEN_LED_1:
        bits[ORDEN_LED_1.index(char)] = True
    elif char in ORDEN_LED_2:
        bits[ORDEN_LED_2.index(char)] = True
    elif char in ORDEN_LED_3:
        bits[ORDEN_LED_3.index(char)] = True

    leds_off()
    send_bits(bits)

    if char in FILA_1:
        fila1.value(1)
    elif char in FILA_2:
        fila2.value(1)
    elif char in FILA_3:
        fila3.value(1)

def buzzer_on():
    buzzer.freq(600)
    buzzer.duty_u16(32768) #Controlar volumen

def buzzer_off():
    buzzer.duty_u16(0)

def reproducir_frase(frase):
    PUNTO = UNIT_TIME
    RAYA  = UNIT_TIME * 3
    GAP_SIMBOLO  = UNIT_TIME
    GAP_CARACTER = UNIT_TIME * 3
    GAP_PALABRA  = UNIT_TIME * 7

    for i, ch in enumerate(frase.upper()):
        if ch == ' ':
            leds_off()
            utime.sleep_ms(GAP_PALABRA)
            continue
        if ch not in MORSE:
            continue

        codigo = MORSE[ch]
        encender_led(ch)

        for j, simbolo in enumerate(codigo):
            buzzer_on()
            utime.sleep_ms(PUNTO if simbolo == '.' else RAYA)
            buzzer_off()
            if j < (len(codigo) - 1):
                utime.sleep_ms(GAP_SIMBOLO)

        leds_off()

        if i < (len(frase) - 1) and frase[i + 1] != ' ':
            utime.sleep_ms(GAP_CARACTER)

while True:
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        linea = sys.stdin.readline().strip()
        if linea.startswith("FRASE:"):
            frase = linea[6:]
            reproducir_frase(frase)

    if button.value() == 1:
        press_start = utime.ticks_ms()
        buzzer_on()
        while button.value() == 1:
            utime.sleep_ms(10)
        buzzer_off()
        duration = utime.ticks_diff(utime.ticks_ms(), press_start)
        if duration < UNIT_TIME * 2:
            print("DOT")
        else:
            print("DASH")