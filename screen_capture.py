import socket
import time
from mss import mss
from PIL import Image
from io import BytesIO

# Configuration
HOST = "192.168.86.49"  # Replace with your Raspberry Pi's IP address
PORT = 5000
CAPTURE_REGION = {"top": 0, "left": 0, "width": 240, "height": 240}  # Adjust capture area
JPEG_QUALITY = 50  # Lower quality for faster transmission

def send_image(client, image):
    """Send an image to the Pi over the socket."""
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    buffer.seek(0)

    # Get the image size
    image_data = buffer.read()
    image_size = len(image_data)

    # Send the size header (8 bytes)
    client.sendall(image_size.to_bytes(8, byteorder="big"))

    # Send the image data
    client.sendall(image_data)

# Connect to the Pi
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    try:
        client.connect((HOST, PORT))
        print(f"Connected to {HOST}:{PORT}")

        with mss() as sct:
            while True:
                # Capture the screen
                screenshot = sct.grab(CAPTURE_REGION)
                image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

                # Send the image to the Pi
                try:
                    send_image(client, image)
                except BrokenPipeError:
                    print("Connection lost. Exiting...")
                    break

                time.sleep(0.03)  # Adjust for refresh rate
    except ConnectionRefusedError:
        print(f"Could not connect to {HOST}:{PORT}")
