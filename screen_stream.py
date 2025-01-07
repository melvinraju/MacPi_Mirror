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
USE_UDP = True  # Set to True for UDP, False for TCP
INACTIVITY_TIMEOUT = 5  # Time in seconds to trigger waiting screen

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


def receive_udp_image(server):
    """Receive and decompress an image over UDP."""
    try:
        server.settimeout(1)
        data, addr = server.recvfrom(65535)

        if not data:
            return False

        decompressed_data = zlib.decompress(data)
        image = Image.open(BytesIO(decompressed_data))
        show_image(disp, image)

        return True
    except socket.timeout:
        return False
    except Exception as e:
        print(f"Error receiving UDP image: {e}")
        return False


def receive_tcp_image(conn):
    """Receive and decompress an image over TCP."""
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

        decompressed_data = zlib.decompress(received_data)
        image = Image.open(BytesIO(decompressed_data))
        show_image(disp, image)

        return True
    except Exception as e:
        print(f"Error receiving TCP image: {e}")
        return None, False


# === MAIN SERVER LOOP (Handles Inactivity) ===
last_frame_time = time.time()

while True:
    try:
        with socket.socket(socket.AF_INET,
                           socket.SOCK_DGRAM if USE_UDP else socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((HOST, PORT))

            if not USE_UDP:
                server.listen(1)

            print(f"{hostname} - {get_wifi_ssid()} - Waiting for stream...")

            display_waiting_message()

            while True:
                if USE_UDP:
                    # Handle UDP reception
                    received = receive_udp_image(server)
                    if received:
                        last_frame_time = time.time()
                else:
                    # Handle TCP reception
                    conn, addr = server.accept()
                    print(f"TCP Connection from {addr}")

                    with conn:
                        while True:
                            keep_alive = receive_tcp_image(conn)
                            if not keep_alive:
                                print("TCP Client disconnected.")
                                break

                # Handle inactivity and return to waiting screen
                if time.time() - last_frame_time > INACTIVITY_TIMEOUT:
                    print("No data received. Returning to waiting screen...")
                    display_waiting_message()
                    last_frame_time = time.time()

    except Exception as e:
        print(f"Server error: {e}")
