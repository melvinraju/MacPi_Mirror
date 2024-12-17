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
    # Receive the image size
    size_data = conn.recv(8)
    if not size_data:
        return None

    image_size = int.from_bytes(size_data, byteorder="big")
    received_data = b""

    while len(received_data) < image_size:
        chunk = conn.recv(4096)
        if not chunk:
            break
        received_data += chunk

    if len(received_data) != image_size:
        print(f"Error: Expected {image_size} bytes, but received {len(received_data)} bytes")
        return None

    return received_data

# Start the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"Server listening on {HOST}:{PORT}")

    conn, addr = server.accept()
    print(f"Connection from {addr}")

    with conn:
        while True:
            try:
                image_data = receive_image(conn)
                if not image_data:
                    break

                # Process and display the image
                try:
                    image = Image.open(BytesIO(image_data))
                    resized_image = image.resize((disp.width, disp.height))
                    rotated_image = resized_image.rotate(270)
                    disp.ShowImage(rotated_image)
                except Exception as e:
                    print(f"Error processing image: {e}")

            except Exception as e:
                print(f"Error: {e}")
                break
