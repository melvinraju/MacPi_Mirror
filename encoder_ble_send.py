import RPi.GPIO as GPIO
from bleak import BleakClient, BleakScanner
import asyncio
import time

CLK = 4
DT = 17
SW = 22

SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "Figproxy_Receiver"

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
        
        last_clk_state = GPIO.input(CLK)
        old_position = position

        while True:
            clk_state = GPIO.input(CLK)
            dt_state = GPIO.input(DT)
            sw_state = GPIO.input(SW)

            if clk_state != last_clk_state:
                if dt_state != clk_state:
                    position += 1
                else:
                    position -= 1

                if position != old_position:
                    if position > old_position:
                        await client.write_gatt_char(CHARACTERISTIC_UUID, b'C', response=True)  # Write with Response
                        print("C")
                    else:
                        await client.write_gatt_char(CHARACTERISTIC_UUID, b'A', response=True)  # Write with Response
                        print("A")

                    old_position = position
                last_clk_state = clk_state

            if sw_state == GPIO.LOW:
                await client.write_gatt_char(CHARACTERISTIC_UUID, b'P', response=True)
                print("P")
                time.sleep(0.5)

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
