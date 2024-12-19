import socket
import time
import argparse
from mss import mss
from PIL import Image
from io import BytesIO

# Function to send an image and rotation metadata
def send_image(client, image, quality, rotation, target_width, target_height):
    """Resize and send an image along with rotation metadata to the Pi over the socket."""
    # Resize the image to the target dimensions
    resized_image = image.resize((target_width, target_height))

    buffer = BytesIO()
    resized_image.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)

    # Get the image size
    image_data = buffer.read()
    image_size = len(image_data)

    # Send the rotation (4 bytes) and size (8 bytes)
    client.sendall(rotation.to_bytes(4, byteorder="big"))
    client.sendall(image_size.to_bytes(8, byteorder="big"))

    # Send the image data
    client.sendall(image_data)

# Main script
def main(host, port, region, timesleep, quality, rotation, target_width, target_height):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((host, port))
            print(f"Connected to {host}:{port}")

            with mss() as sct:
                while True:
                    # Capture the screen
                    screenshot = sct.grab(region)
                    image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

                    # Send the image to the Pi
                    try:
                        send_image(client, image, quality, rotation, target_width, target_height)
                    except BrokenPipeError:
                        print("Connection lost. Exiting...")
                        break

                    time.sleep(timesleep)  # Adjust for refresh rate
    except ConnectionRefusedError:
        print(f"Could not connect to {host}:{port}")

# Command-line argument parser
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream a portion of your screen to a Raspberry Pi.")
    parser.add_argument("--host", type=str, required=True, help="Raspberry Pi IP address")
    parser.add_argument("--port", type=int, default=5000, help="Port number (default: 5000)")
    parser.add_argument("--top", type=int, default=0, help="Top coordinate of the capture region")
    parser.add_argument("--left", type=int, default=0, help="Left coordinate of the capture region")
    parser.add_argument("--width", type=int, default=240, help="Width of the capture region")
    parser.add_argument("--height", type=int, default=240, help="Height of the capture region")
    parser.add_argument("--target-width", type=int, default=240, help="Width of the resized image for the Pi")
    parser.add_argument("--target-height", type=int, default=240, help="Height of the resized image for the Pi")
    parser.add_argument("--timesleep", type=float, default=0.1, help="Time (in seconds) between frames (default: 0.1)")
    parser.add_argument("--quality", type=int, default=50, help="JPEG quality (1-100, default: 50)")
    parser.add_argument("--rotation", type=int, default=0, help="Rotation angle in degrees (default: 0)")

    args = parser.parse_args()

    # Define capture region
    capture_region = {
        "top": args.top,
        "left": args.left,
        "width": args.width,
        "height": args.height,
    }

    # Run the main function
    main(
        args.host,
        args.port,
        capture_region,
        args.timesleep,
        args.quality,
        args.rotation,
        args.target_width,
        args.target_height,
    )
