import RPi.GPIO as GPIO
from bluepy import btle
import time

# GPIO Pins for Encoder
CLK = 4   # GPIO 4
DT = 17   # GPIO 17
SW = 22   # GPIO 22

# Encoder State
last_clk_state = GPIO.LOW

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# Bluetooth Connection to ESP32 (Figproxy_Receiver)
class FigproxyBLE(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def send_data(self, data):
        try:
            characteristic.write(data.encode(), withResponse=True)
            print(f"Sent: {data}")
        except Exception as e:
            print(f"Failed to send: {e}")


def find_and_connect():
    scanner = btle.Scanner().withDelegate(FigproxyBLE())
    print("Scanning for Figproxy_Receiver...")
    devices = scanner.scan(5.0)

    for dev in devices:
        for (adtype, desc, value) in dev.getScanData():
            if desc == "Complete Local Name" and value == "Figproxy_Receiver":
                print(f"Found: {dev.addr}")
                return btle.Peripheral(dev.addr)
    raise Exception("Figproxy_Receiver not found.")


try:
    peripheral = find_and_connect()
    service = peripheral.getServiceByUUID("4fafc201-1fb5-459e-8fcc-c5c9c331914b")
    characteristic = service.getCharacteristics("beb5483e-36e1-4688-b7f5-ea07361b26a8")[0]
    delegate = FigproxyBLE()
    peripheral.withDelegate(delegate)

    last_clk_state = GPIO.input(CLK)

    while True:
        clk_state = GPIO.input(CLK)
        dt_state = GPIO.input(DT)
        sw_state = GPIO.input(SW)

        if clk_state != last_clk_state:
            if dt_state != clk_state:
                delegate.send_data("C")  # Clockwise
            else:
                delegate.send_data("A")  # Anticlockwise
            last_clk_state = clk_state

        if sw_state == GPIO.LOW:
            delegate.send_data("P")  # Button Press
            time.sleep(0.2)  # Debounce

        time.sleep(0.01)

except KeyboardInterrupt:
    GPIO.cleanup()
    peripheral.disconnect()
    print("Disconnected.")
except Exception as e:
    print(f"Error: {e}")
    GPIO.cleanup()
