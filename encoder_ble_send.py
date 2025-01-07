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

position = 0
old_position = 0
last_clk_state = 0
debounce_time = 0.003  # 3 ms debounce for encoder


async def connect_to_m5dial():
    global last_clk_state, position, old_position
    print("Scanning for Figproxy_Receiver...")

    while True:
        try:
            device = await BleakScanner.find_device_by_name(DEVICE_NAME)

            if device:
                print(f"Found {DEVICE_NAME}, attempting to connect...")
                async with BleakClient(device) as client:
                    print(f"Connected to {DEVICE_NAME}")
                    
                    last_clk_state = GPIO.input(CLK)

                    while True:
                        await handle_encoder(client)
                        await asyncio.sleep(0.001)  # Fast polling loop

        except BleakError as e:
            print(f"Connection failed: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)


async def handle_encoder(client):
    global last_clk_state, position, old_position

    clk_state = GPIO.input(CLK)
    dt_state = GPIO.input(DT)

    # Detect leading-edge (CLK falling)
    if clk_state == 0 and last_clk_state == 1:
        # Determine direction based on DT state
        if dt_state == 1:
            position += 1  # Clockwise
            await client.write_gatt_char(CHARACTERISTIC_UUID, b'C', response=True)
            print("C", end="", flush=True)
        else:
            position -= 1  # Anticlockwise
            await client.write_gatt_char(CHARACTERISTIC_UUID, b'A', response=True)
            print("A", end="", flush=True)

    # Update last state for next loop iteration
    last_clk_state = clk_state

    # Button Press (with debounce)
    if GPIO.input(SW) == GPIO.LOW:
        await asyncio.sleep(0.3)  # 300 ms debounce for button
        if GPIO.input(SW) == GPIO.LOW:  # Check again after debounce
            await client.write_gatt_char(CHARACTERISTIC_UUID, b'P', response=True)
            print("P", end="", flush=True)
            time.sleep(0.5)  # Additional debounce


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
