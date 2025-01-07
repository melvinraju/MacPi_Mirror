#!/usr/bin/python3
import socket
from PIL import Image
from io import BytesIO
import os
import time
from lib import LCD_1inch54


# Initialize the display and set backlight to 100%
disp = LCD_1inch54.LCD_1inch54()
disp.Init()
disp.clear()
disp.bl_DutyCycle(100)  # Backlight always at 100%

HOST = "0.0.0.0"
PORT = 5000
hostname = os.uname()[1]


def receive_image(server):
    """Receive an image over UDP."""
    try:
        size_data, addr = server.recvfrom(8)
        if not size_data or len(size_data) < 8:
            return None, False

        image_size = int.from_bytes(size_data, byteorder="big")
        received_data = b""
        while len(received_data) < image_size:
            chunk, _ = server.recvfrom(4096)
            received_data += chunk

        return received_data, True
    except Exception as e:
        return None, False


while True:
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind((HOST, PORT))
        server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1048576)  # 1 MB receive buffer
        print(f"{hostname} - Waiting for stream...")

        while True:
            image_data, keep_alive = receive_image(server)
            if not keep_alive:
                continue

            try:
                start_time = time.time()
                image = Image.open(BytesIO(image_data))
                disp.ShowImage(image)
                end_time = time.time()

                print(f"Frame displayed in {end_time - start_time:.2f} seconds")
            except Exception as e:
                print(f"Error displaying image: {e}")
                continue
    except Exception as e:
        print(f"Server error: {e}")
