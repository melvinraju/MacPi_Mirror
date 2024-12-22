import socket
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from lib import LCD_1inch54  # Adjust for your library

# Initialize the display and set backlight to 100%
disp = LCD_1inch54.LCD_1inch54()
disp.Init()
disp.clear()
disp.bl_DutyCycle(100)  # Backlight at 100%


HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 5000       # Port for incoming data


def receive_image(conn):
    """Receive an image over the socket connection."""
    try:
        # Receive the image size (8 bytes)
        size_data = conn.recv(8)
        if not size_data or len(size_data) < 8:
            print("No data received. Client may have disconnected.")
            return None, False

        image_size = int.from_bytes(size_data, byteorder="big")
        print(f"Expecting image of size: {image_size} bytes.")

        # Receive the image data in chunks
        received_data = b""
        while len(received_data) < image_size:
            chunk = conn.recv(min(4096, image_size - len(received_data)))
            if not chunk:
                print("Connection lost while receiving image data.")
                return None, False
            received_data += chunk

        # Handle incomplete data
        if len(received_data) != image_size:
            print(f"Error: Expected {image_size} bytes, but received {len(received_data)} bytes. Skipping frame.")
            return None, True  # Keep connection alive but skip this frame

        return received_data, True
    except Exception as e:
        print(f"Exception during receive_image: {e}")
        return None, False


def display_waiting_message():
    """Display 'Waiting for connection...' message with a default font."""
    image = Image.new("RGB", (disp.width, disp.height), "BLACK")
    draw = ImageDraw.Draw(image)

    # Always use the default Pillow font (guaranteed to be available)
    font = ImageFont.load_default()
    message = "Waiting for\nconnection..."

    # Center the text using bounding box
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


# Start the server
while True:
    try:
        display_waiting_message()
        print("Waiting for connection...")

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
                        continue  # Skip to next frame if the current one is incomplete

                    # Display the received image
                    try:
                        image = Image.open(BytesIO(image_data))
                        disp.ShowImage(image)
                    except Exception as e:
                        print(f"Error displaying image: {e}")
                        continue
    except Exception as e:
        print(f"Server error: {e}")
