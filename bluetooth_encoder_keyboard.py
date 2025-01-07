import RPi.GPIO as GPIO
import time
import pyautogui
import bluetooth

# Pin Definitions
CLK_PIN = 4
DT_PIN = 17
SW_PIN = 22

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Variables
counter = 0
last_clk_state = GPIO.input(CLK_PIN)

def button_press(channel):
    pyautogui.press('p')
    print("Button pressed! Sent 'P'")

# Attach event for button press
GPIO.add_event_detect(SW_PIN, GPIO.FALLING, callback=button_press, bouncetime=300)

try:
    print("Bluetooth Keyboard Running...")

    while True:
        clk_state = GPIO.input(CLK_PIN)
        dt_state = GPIO.input(DT_PIN)

        # Detect rotation
        if clk_state != last_clk_state:
            if dt_state != clk_state:
                pyautogui.press('c')
                print("Rotated Clockwise! Sent 'C'")
            else:
                pyautogui.press('a')
                print("Rotated Anticlockwise! Sent 'A'")

        # Update last clk state
        last_clk_state = clk_state

        # Small delay to prevent bouncing
        time.sleep(0.01)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    GPIO.cleanup()
