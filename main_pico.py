from machine import Pin
import utime

BUTTON_PIN = 16

UNIT_TIME = 300

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)

while True:
    while button.value() == 0:
        utime.sleep_ms(10)

    press_start = utime.ticks_ms()

    while button.value() == 1:
        utime.sleep_ms(10)

    duration = utime.ticks_diff(utime.ticks_ms(), press_start)

    if duration < UNIT_TIME:
        print("DOT")
    else:
        print("DASH")