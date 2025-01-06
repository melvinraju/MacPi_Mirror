import RPi.GPIO as GPIO
from bleak import BleakClient, BleakScanner
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

# Track encoder position
encoder_position = 0
old_position = 0

# Track button state
last_button_state = GPIO.HIGH


# Function to read the encoder position
def read_encoder():
    global encoder_position
    clk_state = GPIO.input(CLK)
    dt_state = GPIO.input(DT)

    # Detect rotation direction
    if clk_state == GPIO.LOW:
        if dt_state == GPIO.HIGH:
            encoder_position += 1  # Clockwise
        else:
            encoder_position -= 1  # Anticlockwise


# Asynchronous BLE connection and write function
async def connect_to_m5dial():
    device = await BleakScanner.find_device_by_name(DEVICE_NAME)
    if not device:
        raise Exception(f"Device {DEVICE_NAME} not found.")

    async with BleakClient(device) as client:
        print(f"Connected to {DEVICE_NAME}")

        global old_position, last_button_state

        while True:
            read_encoder()
            new_position = encoder_position // 2  # Divide by 2 for detent handling

            # Detect rotation (Only send if position changes)
            if new_position != old_position:
                if new_position > old_position:
                    await client.write_gatt_char(CHARACTERISTIC_UUID, b'C')  # Clockwise
                    print("C", end="", flush=True)
                else:
                    await client.write_gatt_char(CHARACTERISTIC_UUID, b'A')  # Anticlockwise
                    print("A", end="", flush=True)
                old_position = new_position

            # Detect button press (Only on falling edge)
            button_state = GPIO.input(SW)
            if button_state == GPIO.LOW and last_button_state == GPIO.HIGH:
                await client.write_gatt_char(CHARACTERISTIC_UUID, b'P')
                print("P", end="", flush=True)
                time.sleep(0.2)  # Simple debounce

            last_button_state = button_state  # Update button state

            await asyncio.sleep(0.01)


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
        print("Disconnected.")
        GPIO.cleanup()
