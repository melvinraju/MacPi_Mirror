import RPi.GPIO as GPIO
from bleak import BleakClient, BleakScanner, BleakError
import asyncio
import time

# GPIO Pins for Encoder
CLK = 4
DT = 17
SW = 22

# UUIDs for BLE Service and Characteristic
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "Figproxy_Receiver"

# Track encoder state
last_state = 0
position = 0
old_position = 0
debounce_time = 0.001  # Encoder debounce


async def connect_to_m5dial():
    global last_state, position, old_position
    print("Scanning for Figproxy_Receiver...")

    while True:
        try:
            device = await BleakScanner.find_device_by_name(DEVICE_NAME)

            if device:
                print(f"Found {DEVICE_NAME}, attempting to connect...")
                async with BleakClient(device) as client:
                    print(f"Connected to {DEVICE_NAME}")
                    
                    last_state = (GPIO.input(CLK) << 1) | GPIO.input(DT)

                    while True:
                        await handle_encoder(client)
                        await asyncio.sleep(0.001)

        except BleakError as e:
            print(f"Connection failed: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)


async def handle_encoder(client):
    global last_state, position, old_position

    # Read current state of CLK and DT
    current_state = (GPIO.input(CLK) << 1) | GPIO.input(DT)

    # Detect rotation by comparing current state to the last known state
    if current_state != last_state:
        if ((last_state == 0b00 and current_state == 0b01) or
            (last_state == 0b01 and current_state == 0b11) or
            (last_state == 0b11 and current_state == 0b10) or
            (last_state == 0b10 and current_state == 0b00)):
            position += 1  # Clockwise

        elif ((last_state == 0b00 and current_state == 0b10) or
              (last_state == 0b10 and current_state == 0b11) or
              (last_state == 0b11 and current_state == 0b01) or
              (last_state == 0b01 and current_state == 0b00)):
            position -= 1  # Anticlockwise

        # Update state
        last_state = current_state

        # Send BLE signal if position changed
        if position != old_position:
            if position > old_position:
                await client.write_gatt_char(CHARACTERISTIC_UUID, b'C', response=True)
                print("C")
            else:
                await client.write_gatt_char(CHARACTERISTIC_UUID, b'A', response=True)
                print("A")
            old_position = position


def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)


if __name__ == "__main__":
    setup_gpio()
    try:
        asyncio.run(connect_to_m5dial())
    except KeyboardInterrupt:
        print("\nDisconnected.")
        GPIO.cleanup()
