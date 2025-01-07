import RPi.GPIO as GPIO
import time
from evdev import UInput, ecodes as e

# Pin Definitions
CLK_PIN = 4
DT_PIN = 17
SW_PIN = 22

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize UInput for HID keyboard
ui = UInput()

# Variables
counter = 0
last_clk_state = GPIO.input(CLK_PIN)

def send_key(key):
    ui.write(e.EV_KEY, key, 1)  # Key press
    ui.write(e.EV_KEY, key, 0)  # Key release
    ui.syn()  # Synchronize events
    print(f"Sent key: {key}")

def button_press(channel):
    send_key(e.KEY_P)  # Send 'P' on button press

# Attach event for button press
GPIO.add_event_detect(SW_PIN, GPIO.FALLING, callback=button_press, bouncetime=300)

try:
    print("Bluetooth Keyboard Running...")

    while True:
        clk_state = GPIO.input(CLK_PIN)
        dt_state = GPIO.input(DT_PIN)

        if clk_state != last_clk_state:
            if dt_state != clk_state:
                send_key(e.KEY_C)  # Send 'C' for clockwise
            else:
                send_key(e.KEY_A)  # Send 'A' for anticlockwise

        last_clk_state = clk_state
        time.sleep(0.01)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    GPIO.cleanup()
    ui.close()
