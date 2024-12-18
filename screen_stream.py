import socket
from PIL import Image
from io import BytesIO
from lib import LCD_1inch54  # Adjust for your library

# Initialize the display
disp = LCD_1inch54.LCD_1inch54()
disp.Init()
disp.clear()
disp.bl_DutyCycle(50)  # Set backlight

# Network configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 5000       # Port for incoming data

def receive_image(conn):
    """Receive an image over the socket connection."""
    try:
        # Receive the image size (8 bytes)
        size_data = conn.recv(8)
        if not size_data or len(size_data) < 8:
            print("No data received or incomplete size header. Client may have disconnected.")
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

        if len(received_data) != image_size:
            print(f"Error: Expected {image_size} bytes, but received {len(received_data)} bytes. Skipping frame.")
            return None, True  # Skip frame but keep the connection alive

        return received_data, True
    except Exception as e:
        print(f"Exception during receive_image: {e}")
        return None, False

def display_waiting_message():
    """Display 'Waiting for connection...' message on the screen."""
    from PIL import ImageDraw, ImageFont
    image = Image.new("RGB", (disp.width, disp.height), "BLACK")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except IOError:
        font = ImageFont.load_default()  # Fallback to default if custom font is unavailable

    message = "Waiting for\nconnection..."
    bbox = draw.multiline_textbbox((0, 0), message, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.multiline_text(((disp.width - w) // 2, (disp.height - h) // 2), message, fill="WHITE", font=font, align="center")

    disp.ShowImage(image)

# Start the server
while True:
    try:
        # Display waiting message
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
                    # Attempt to receive and process an image
                    image_data, keep_alive = receive_image(conn)
                    if not keep_alive:
                        print("Client disconnected.")
                        break  # Exit to wait for a new connection

                    if image_data is None:
                        # Skip the frame but retain the last valid image on the display
                        print("Skipped a frame. Continuing...")
                        continue

                    # Process and display the valid image
                    try:
                        image = Image.open(BytesIO(image_data))
                        resized_image = image.resize((disp.width, disp.height))
                        rotated_image = resized_image.rotate(270)
                        disp.ShowImage(rotated_image)
                    except Exception as e:
                        print(f"Error processing image: {e}")
                        continue

    except Exception as e:
        print(f"Server error: {e}")
