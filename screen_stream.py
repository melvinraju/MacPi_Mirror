#!/usr/bin/python3
import socket
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import subprocess
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


def get_wifi_ssid():
    try:
        ssid = subprocess.check_output(
            ["iwgetid", "-r"], stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        return f"WiFi: {ssid}" if ssid else "WiFi: Not connected"
    except subprocess.CalledProcessError:
        return "WiFi: Not connected"


def receive_image(conn):
    try:
        size_data = conn.recv(8)
        if not size_data or len(size_data) < 8:
            return None, False

        image_size = int.from_bytes(size_data, byteorder="big")
        received_data = b""
        while len(received_data) < image_size:
            chunk = conn.recv(min(4096, image_size - len(received_data)))
            if not chunk:
                return None, False
            received_data += chunk

        return received_data, True
    except Exception as e:
        return None, False


while True:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((HOST, PORT))
            server.listen(1)

            while True:
                conn, addr = server.accept()
                with conn:
                    while True:
                        image_data, keep_alive = receive_image(conn)
                        if not keep_alive:
                            break

                        if image_data is None:
                            continue

                        try:
                            start_time = time.time()
                            image = Image.open(BytesIO(image_data))
                            disp.ShowImage(image)
                            end_time = time.time()

                            print(f"Frame displayed in {end_time - start_time:.2f} seconds")
                        except Exception as e:
                            continue
    except Exception as e:
        print(f"Server error: {e}")
