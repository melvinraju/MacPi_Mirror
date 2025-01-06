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
last_clk_state = 0

async def connect_to_m5dial():
    global encoder_position, old_position, last_clk_state

    # Connect to BLE device
    device = await BleakScanner.find_device_by_name(DEVICE_NAME)
    if not device:
        raise Exception(f"Device {DEVICE_NAME} not found.")

    async with BleakClient(device) as client:
        print(f"Connected to {DEVICE_NAME}")

        # Initialize last CLK state
        last_clk_state = GPIO.input(CLK)
        old_position = encoder_position  # Initial position

        while True:
            clk_state = GPIO.input(CLK)
            dt_state = GPIO.input(DT)

            # Detect direction
            if clk_state != last_clk_state:
                # Determine if rotating clockwise or anticlockwise
                if dt_state != clk_state:
                    encoder_position += 1  # Clockwise
                else:
                    encoder_position -= 1  # Anticlockwise

                last_clk_state = clk_state  # Update for next cycle

            # Send data only if the position has changed
            if encoder_position != old_position:
                if encoder_position > old_position:
                    await client.write_gatt_char(CHARACTERISTIC_UUID, b'C')  # Clockwise
                else:
                    await client.write_gatt_char(CHARACTERISTIC_UUID, b'A')  # Anticlockwise

                old_position = encoder_position  # Update last known position

            # Button press detection
            if GPIO.input(SW) == GPIO.LOW:
                await client.write_gatt_char(CHARACTERISTIC_UUID, b'P')  # Button Press
                time.sleep(0.2)  # Simple debounce

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
