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
position = 0
old_position = 0
last_clk_state = 0


async def connect_to_m5dial():
    global last_clk_state, position, old_position
    device = await BleakScanner.find_device_by_name(DEVICE_NAME)
    if not device:
        raise Exception(f"Device {DEVICE_NAME} not found.")

    async with BleakClient(device) as client:
        print(f"Connected to {DEVICE_NAME}")
        
        # Initialize last_clk_state
        last_clk_state = GPIO.input(CLK)
        old_position = position // 2  # Initialize old position

        while True:
            clk_state = GPIO.input(CLK)
            dt_state = GPIO.input(DT)
            sw_state = GPIO.input(SW)

            # Detect encoder rotation
            if clk_state != last_clk_state:
                if dt_state != clk_state:
                    position += 1  # Clockwise
                else:
                    position -= 1  # Anticlockwise

                # Divide by 2 to stabilize
                new_position = position // 2

                if new_position != old_position:
                    if new_position > old_position:
                        await client.write_gatt_char(CHARACTERISTIC_UUID, b'C')  # Clockwise
                        print("C")  # Print on new line
                    else:
                        await client.write_gatt_char(CHARACTERISTIC_UUID, b'A')  # Anticlockwise
                        print("A")  # Print on new line

                    old_position = new_position  # Update old position

                last_clk_state = clk_state

            # Detect button press
            if sw_state == GPIO.LOW:
                await client.write_gatt_char(CHARACTERISTIC_UUID, b'P')  # Button Press
                print("P")  # Print button press
                time.sleep(0.5)  # Debounce

            await asyncio.sleep(0.001)


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
