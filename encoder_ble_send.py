import RPi.GPIO as GPIO
from bleak import BleakClient, BleakScanner, BleakError
import asyncio
import time

# GPIO Pins
CLK = 4
DT = 17
ENCODER_BUTTON = 22  # Encoder button (sends "P")
L_BUTTON = 23        # L_Button (sends "L")
O_BUTTON = 24        # O_Button (sends "O")

# UUIDs for BLE Service and Characteristic
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "Figproxy_Receiver"

# Encoder state tracking
position = 0
old_position = 0
last_clk_state = 0
last_direction = None  # Track last direction

# Debounce timing
encoder_debounce_time = 0.002  # 2 ms debounce for encoder
button_debounce_time = 0.05   # 50 ms debounce for buttons


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
                    old_position = position

                    while True:
                        await handle_inputs(client)
                        await asyncio.sleep(0.001)

        except asyncio.TimeoutError:
            print(f"Connection attempt to {DEVICE_NAME} timed out. Retrying in 2 seconds...")
            await asyncio.sleep(2)
        except BleakError as e:
            print(f"BLE error: {e}. Retrying in 2 seconds...")
            await asyncio.sleep(2)


async def handle_inputs(client):
    global last_clk_state, position, old_position, last_direction

    clk_state = GPIO.input(CLK)
    dt_state = GPIO.input(DT)
    encoder_button_state = GPIO.input(ENCODER_BUTTON)
    l_button_state = GPIO.input(L_BUTTON)
    o_button_state = GPIO.input(O_BUTTON)

    # Debounce Encoder
    if clk_state != last_clk_state:
        await asyncio.sleep(encoder_debounce_time)

        clk_state = GPIO.input(CLK)
        if clk_state != last_clk_state:
            if dt_state != clk_state:  # Clockwise
                if last_direction == 'CCW':
                    position += 1  # Ignore the first detent after switching to CW
                else:
                    position += 1
                last_direction = 'CW'
            elif dt_state == clk_state:  # Anticlockwise
                if last_direction == 'CW':
                    position -= 1  # Ensure first detent is processed after switching to CCW
                else:
                    position -= 1
                last_direction = 'CCW'

            # Ensure one print per detent by dividing by 2
            new_position = position // 2  

            if new_position != old_position:
                if new_position > old_position:
                    await client.write_gatt_char(CHARACTERISTIC_UUID, b'C', response=True)
                    print("C")
                else:
                    await client.write_gatt_char(CHARACTERISTIC_UUID, b'A', response=True)
                    print("A")

                old_position = new_position
            last_clk_state = clk_state

    # Debounce Encoder Button (P)
    if encoder_button_state == GPIO.LOW:
        await asyncio.sleep(button_debounce_time)
        if GPIO.input(ENCODER_BUTTON) == GPIO.LOW:
            await client.write_gatt_char(CHARACTERISTIC_UUID, b'P', response=True)
            print("P")
            time.sleep(0.05)  # Additional debounce for encoder button

    # Debounce L_Button (L)
    if l_button_state == GPIO.LOW:
        await asyncio.sleep(button_debounce_time)
        if GPIO.input(L_BUTTON) == GPIO.LOW:
            await client.write_gatt_char(CHARACTERISTIC_UUID, b'L', response=True)
            print("L")
            time.sleep(0.05)  # Additional debounce for L_Button

    # Debounce O_Button (O)
    if o_button_state == GPIO.LOW:
        await asyncio.sleep(button_debounce_time)
        if GPIO.input(O_BUTTON) == GPIO.LOW:
            await client.write_gatt_char(CHARACTERISTIC_UUID, b'O', response=True)
            print("O")
            time.sleep(0.05)  # Additional debounce for O_Button


def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ENCODER_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Setup encoder button
    GPIO.setup(L_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Setup L_Button
    GPIO.setup(O_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Setup O_Button


if __name__ == "__main__":
    setup_gpio()
    try:
        asyncio.run(connect_to_m5dial())
    except KeyboardInterrupt:
        print("\nDisconnected.")
        GPIO.cleanup()
