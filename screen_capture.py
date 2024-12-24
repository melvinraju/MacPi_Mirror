import socket
import time
import argparse
from mss import mss
from PIL import Image
from io import BytesIO


def send_image(client, image, quality, rotation, target_width, target_height):
    """Resize, rotate, and send an image to the Pi over the socket."""
    image = image.resize((target_width, target_height), Image.LANCZOS).rotate(rotation)

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True, subsampling=0)
    buffer.seek(0)

    image_data = buffer.read()
    image_size = len(image_data)

    # Send the image size (8 bytes)
    client.sendall(image_size.to_bytes(8, byteorder="big"))

    # Send the image data in one batch
    client.sendall(image_data)


def resolve_hostname(hostname):
    """Resolve hostname to IP address."""
    try:
        return socket.gethostbyname(f"{hostname}.local")
    except socket.gaierror:
        print(f"Failed to resolve hostname: {hostname}")
        return None


def main(hostname, port, region, framerate, quality, rotation, target_width, target_height):
    delay = 1 / framerate  # Convert framerate to delay between frames
    host = resolve_hostname(hostname)

    if not host:
        print("Could not resolve the hostname. Exiting...")
        return

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Low latency
            client.connect((host, port))
            print(f"Connected to {hostname} ({host}):{port}")

            with mss() as sct:
                while True:
                    # Capture the screen and convert to PIL Image
                    screenshot = sct.grab(region)
                    image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

                    # Send the image to the Pi
                    try:
                        send_image(client, image, quality, rotation, target_width, target_height)
                    except (BrokenPipeError, ConnectionResetError):
                        print("Connection lost. Exiting...")
                        break

                    time.sleep(delay)  # Adjust for framerate
    except ConnectionRefusedError:
        print(f"Could not connect to {hostname}:{port}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream a portion of your screen to a Raspberry Pi.")
    parser.add_argument("--hostname", type=str, required=True, help="Hostname of the Raspberry Pi")
    parser.add_argument("--port", type=int, default=5000, help="Port number (default: 5000)")
    parser.add_argument("--top", type=int, default=0, help="Top coordinate of the capture region")
    parser.add_argument("--left", type=int, default=0, help="Left coordinate of the capture region")
    parser.add_argument("--width", type=int, default=240, help="Width of the capture region")
    parser.add_argument("--height", type=int, default=240, help="Height of the capture region")
    parser.add_argument("--target-width", type=int, default=240, help="Width of the resized image for the Pi")
    parser.add_argument("--target-height", type=int, default=240, help="Height of the resized image for the Pi")
    parser.add_argument("--framerate", type=float, default=10, help="Frames per second (default: 10 FPS)")
    parser.add_argument("--quality", type=int, default=50, help="JPEG quality (1-100, default: 50)")
    parser.add_argument("--rotation", type=int, default=0, help="Rotation angle in degrees (default: 0)")

    args = parser.parse_args()

    capture_region = {
        "top": args.top,
        "left": args.left,
        "width": args.width,
        "height": args.height,
    }

    main(
        args.hostname,
        args.port,
        capture_region,
        args.framerate,
        args.quality,
        args.rotation,
        args.target_width,
        args.target_height,
    )
