#!/usr/bin/python3
import socket
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import subprocess
import zlib
import time
from lib import LCD_1inch54

# === DISPLAY FUNCTIONS (CUSTOMIZABLE FOR DIFFERENT LCD LIBRARIES) ===
def init_display():
    display = LCD_1inch54.LCD_1inch54()
    display.Init()
    return display

def clear_display(display):
    display.clear()

def set_backlight(display, brightness):
    display.bl_DutyCycle(brightness)

def show_image(display, image):
    display.ShowImage(image)

# Initialize display and backlight
disp = init_display()
clear_display(disp)
set_backlight(disp, 100)

# === NETWORK CONFIGURATION ===
HOST = "0.0.0.0"
PORT = 5000

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

    # Prepare the message with hostname and Wi-Fi info
    message = f"{hostname}\n{ssid_info}\nWaiting for stream..."

    # Center the text on the screen
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
        # Receive image size (8 bytes)
        size_data = conn.recv(8)
        if not size_data or len(size_data) < 8:
            print("No data received. Client may have disconnected.")
            return None, False

        image_size = int.from_bytes(size_data, byteorder="big")
        print(f"Receiving compressed image of size: {image_size / 1024:.2f} KB...")

        # Receive image data
        received_data = b""
        while len(received_data) < image_size:
            chunk = conn.recv(min(4096, image_size - len(received_data)))
            if not chunk:
                print("Connection lost during image reception.")
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


# === MAIN SERVER LOOP ===
while True:
    try:
        # Create a fresh socket each time we come back to wait for a new client
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((HOST, PORT))
            server.listen(1)

            # Show the waiting screen and block until we get a connection
            display_waiting_message()
            print(f"{hostname} - {get_wifi_ssid()} - Waiting for stream...")

            # accept() will block until a client connects
            conn, addr = server.accept()
            print(f"Connection from {addr}")

            with conn:
                while True:
                    keep_alive = receive_image(conn)
                    if not keep_alive:
                        print("Client disconnected. Returning to waiting screen...")
                        break

            # Once we break from the inner loop, we close conn and
            # go back to the top of the outer while True to rebind
            # and show waiting screen again.

    except Exception as e:
        print(f"Server error: {e}")
        # Sleep briefly to avoid rapid crash loops if something goes wrong
        time.sleep(5)
