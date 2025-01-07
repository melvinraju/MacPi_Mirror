#!/usr/bin/python3
import socket
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import subprocess
import zlib
import time
from lib import LCD_1inch54


def init_display():
    display = LCD_1inch54.LCD_1inch54()
    display.Init()
    return display


def show_image(display, image):
    display.ShowImage(image)


disp = init_display()
disp.clear()
disp.bl_DutyCycle(100)  # Set backlight to 100%


def receive_image(conn):
    try:
        size_data = conn.recv(8)
        if not size_data or len(size_data) < 8:
            return None, False

        image_size = int.from_bytes(size_data, byteorder="big")
        print(f"Receiving compressed image of size: {image_size / 1024:.2f} KB...")

        received_data = b""
        while len(received_data) < image_size:
            chunk = conn.recv(min(4096, image_size - len(received_data)))
            if not chunk:
                return None, False
            received_data += chunk

        # Decompress the image
        decompressed_data = zlib.decompress(received_data)

        start_time = time.time()
        image = Image.open(BytesIO(decompressed_data))
        show_image(disp, image)
        end_time = time.time()

        print(f"Frame displayed in {end_time - start_time:.2f} seconds")

        return True
    except Exception as e:
        print(f"Error receiving image: {e}")
        return None, False


HOST = "0.0.0.0"
PORT = 5000

while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen(1)
        print(f"Waiting for stream on port {PORT}...")

        conn, addr = server.accept()
        print(f"Connection from {addr}")

        with conn:
            while True:
                keep_alive = receive_image(conn)
                if not keep_alive:
                    print("Client disconnected.")
                    break
