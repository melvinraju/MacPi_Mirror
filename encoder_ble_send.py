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
button_debounce_time = 0.1  # 100 ms debounce for button


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

    # Detect both rising and falling edges
    if clk_state != last_clk_state:
        # Determine direction based on DT state during CLK edge
        if clk_state == dt_state:
            position += 1  # Clockwise
            await client.write_gatt_char(CHARACTERISTIC_UUID, b'C', response=True)
            print("C", end="", flush=True)
        else:
            position -= 1  # Anticlockwise
            await client.write_gatt_char(CHARACTERISTIC_UUID, b'A', response=True)
            print("A", end="", flush=True)

        last_clk_state = clk_state

    # Button Press (with reduced debounce)
    if GPIO.input(SW) == GPIO.LOW:
        await asyncio.sleep(button_debounce_time)

        # Re-check after debounce
        if GPIO.input(SW) == GPIO.LOW:
            await client.write_gatt_char(CHARACTERISTIC_UUID, b'P', response=True)
            print("P", end="", flush=True)
            time.sleep(0.2)  # Shorter debounce for faster response


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
