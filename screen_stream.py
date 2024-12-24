import socket
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from lib import LCD_1inch54
import os

# Initialize the display and set backlight to 100%
disp = LCD_1inch54.LCD_1inch54()
disp.Init()
disp.clear()
disp.bl_DutyCycle(100)  # Backlight always at 100%

# Network configuration
HOST = "0.0.0.0"
PORT = 5000

# Get the Pi's hostname
hostname = os.uname()[1]


def receive_image(conn):
    """Receive an image over the socket connection."""
    try:
        size_data = conn.recv(8)
        if not size_data or len(size_data) < 8:
            print("No data received. Client may have disconnected.")
            return None, False

        image_size = int.from_bytes(size_data, byteorder="big")
        print(f"Expecting image of size: {image_size} bytes.")

        received_data = b""
        while len(received_data) < image_size:
            chunk = conn.recv(min(4096, image_size - len(received_data)))
            if not chunk:
                print("Connection lost while receiving image data.")
                return None, False
            received_data += chunk

        if len(received_data) != image_size:
            print(f"Error: Expected {image_size} bytes, but received {len(received_data)} bytes. Skipping frame.")
            return None, True

        return received_data, True
    except Exception as e:
        print(f"Exception during receive_image: {e}")
        return None, False


def display_waiting_message():
    """Display the hostname and 'Waiting for connection...' message."""
    image = Image.new("RGB", (disp.width, disp.height), "BLACK")
    draw = ImageDraw.Draw(image)

    font = ImageFont.load_default()
    message = f"{hostname}\nWaiting for\nconnection..."

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

    disp.ShowImage(image)


while True:
    try:
        display_waiting_message()
        print(f"{hostname} - Waiting for connection...")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((HOST, PORT))
            server.listen(1)

            conn, addr = server.accept()
            print(f"Connection from {addr}")

            with conn:
                while True:
                    image_data, keep_alive = receive_image(conn)
                    if not keep_alive:
                        print("Client disconnected.")
                        break

                    if image_data is None:
                        continue

                    try:
                        image = Image.open(BytesIO(image_data))
                        disp.ShowImage(image)
                    except Exception as e:
                        print(f"Error displaying image: {e}")
                        continue
    except Exception as e:
        print(f"Server error: {e}")
