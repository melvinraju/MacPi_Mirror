#!/usr/bin/python3
import socket
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import subprocess
import zlib
import time
from lib import LCD_1inch54

# === DISPLAY SETUP FUNCTIONS ===
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
        ssid = subprocess.check_output(["iwgetid", "-r"], stderr=subprocess.DEVNULL)
        ssid = ssid.decode("utf-8").strip()
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

    # Center the text
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
    """
    Receive and decompress an image over the socket connection.
    Returns:
      - True if a valid image was received and displayed.
      - None, False if the client disconnected or an error occurred.
    """
    try:
        # Read 8 bytes for the size
        size_data = conn.recv(8)
        if not size_data or len(size_data) < 8:
            print("No data received. Client may have disconnected.")
            return None, False

        image_size = int.from_bytes(size_data, byteorder="big")
        print(f"Receiving compressed image of size: {image_size} bytes.")

        # Read the full compressed image
        received_data = b""
        while len(received_data) < image_size:
            chunk = conn.recv(min(4096, image_size - len(received_data)))
            if not chunk:
                print("Connection lost during image reception.")
                return None, False
            received_data += chunk

        if len(received_data) != image_size:
            print(f"Expected {image_size} bytes, got {len(received_data)} bytes.")
            return None, True  # Keep connection alive but skip

        # Decompress the image
        decompressed_data = zlib.decompress(received_data)

        # Display the image
        image = Image.open(BytesIO(decompressed_data))
        show_image(disp, image)

        return True, True

    except Exception as e:
        print(f"Error receiving image: {e}")
        return None, False


# === MAIN LOOP ===
while True:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            # Allow re-binding the port after a disconnect
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((HOST, PORT))
            server.listen(1)

            print(f"{hostname} - {get_wifi_ssid()} - Waiting for stream...")

            # Outer loop that continuously updates the "waiting" screen
            while True:
                # Show waiting screen every 2 seconds
                display_waiting_message()
                time.sleep(2)

                # Non-blocking accept by setting a 1-second timeout
                server.settimeout(1)
                try:
                    conn, addr = server.accept()
                except socket.timeout:
                    # No new connection, so loop again
                    continue

                print(f"Connection from {addr}")

                with conn:
                    # Inner loop: receive frames until client disconnects
                    while True:
                        frame_result, keep_alive = receive_image(conn)
                        if not keep_alive:
                            print("Client disconnected. Returning to waiting screen...")
                            break
                        if frame_result is None:
                            # Something went wrong with that frame, but keep listening
                            continue

                # After the connection is closed, we return to the waiting loop
                print("Waiting for next connection...")

    except Exception as e:
        print(f"Server error: {e}")
        # Delay to prevent rapid loop restarts if there's a crash
        time.sleep(5)
