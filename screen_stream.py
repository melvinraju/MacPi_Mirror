#!/usr/bin/python3
import socket
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import subprocess
import zlib
import time
from lib import LCD_1inch54


# === DISPLAY FUNCTIONS ===
def init_display():
    display = LCD_1inch54.LCD_1inch54()
    display.Init()
    return display


def show_image(display, image):
    display.ShowImage(image)


# Initialize display
disp = init_display()
disp.clear()
disp.bl_DutyCycle(100)  # Backlight always at 100%

# === NETWORK CONFIGURATION ===
HOST = "0.0.0.0"
PORT = 5000
USE_UDP = False  # Set to True for UDP, False for TCP

# Get the Pi's hostname
hostname = os.uname()[1]


def get_wifi_ssid():
    """Retrieve the Wi-Fi SSID or return 'Not connected' if unavailable."""
    try:
        ssid = subprocess.check_output(
            ["iwgetid", "-r"], stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()

        return f"WiFi: {ssid}" if ssid else "WiFi: Not connected"
    except subprocess.CalledProcessError:
        return "WiFi: Not connected"


def display_waiting_message():
    """Display the hostname, Wi-Fi status, and waiting message on the screen."""
    image = Image.new("RGB", (disp.width, disp.height), "BLACK")
    draw = ImageDraw.Draw(image)

    font = ImageFont.load_default()
    ssid_info = get_wifi_ssid()

    message = f"{hostname}\n{ssid_info}\nWaiting for stream..."

    bbox = draw.multiline_textbbox((0, 0), message, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    draw.multiline_text(
        ((disp.width - w) // 2, (disp.height - h) // 2),
        message,
        fill="WHITE",
        font=font,
        align="center",
    )

    show_image(disp, image)


def receive_image(conn):
    """Receive and decompress an image over the socket connection."""
    try:
        conn.settimeout(5)  # Timeout if no data is received for 5 seconds

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

        decompressed_data = zlib.decompress(received_data)

        start_time = time.time()
        image = Image.open(BytesIO(decompressed_data))
        show_image(disp, image)
        end_time = time.time()

        print(f"Frame displayed in {end_time - start_time:.2f} seconds")

        return True
    except socket.timeout:
        print("No data received. Returning to waiting screen...")
        return None, False
    except Exception as e:
        print(f"Error receiving image: {e}")
        return None, False


# === MAIN SERVER LOOP ===
while True:
    try:
        with socket.socket(socket.AF_INET,
                           socket.SOCK_DGRAM if USE_UDP else socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((HOST, PORT))

            if not USE_UDP:
                server.listen(1)

            print(f"{hostname} - {get_wifi_ssid()} - Waiting for stream...")

            while True:
                display_waiting_message()
                if USE_UDP:
                    server.settimeout(5)
                    try:
                        data, addr = server.recvfrom(65535)
                        print(f"UDP Data received from {addr}")
                        receive_image(server)
                    except socket.timeout:
                        continue
                else:
                    conn, addr = server.accept()
                    print(f"Connection from {addr}")

                    with conn:
                        while True:
                            keep_alive = receive_image(conn)
                            if not keep_alive:
                                print("Client disconnected. Returning to waiting screen...")
                                break

    except Exception as e:
        print(f"Server error: {e}")
