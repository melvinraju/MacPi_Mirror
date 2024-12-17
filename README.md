# MacPi Mirror

### **1. Overview**

- **Mac**: Captures a portion of the screen and sends it to the Raspberry Pi over a network.
- **Raspberry Pi**: Receives the data, processes it, and displays it on an ST7789 LCD.

The scripts use the **Pillow**, **mss**, and **sockets** libraries for capturing, compressing, and transmitting images.

---

### **2. Prerequisites**

- **Hardware**:
  - Raspberry Pi (any model with GPIO and networking capabilities).
  - ST7789 LCD (1.54" 240x240 is used in this demo).
  - A reliable network connection (Wi-Fi or Ethernet).

- **Software**:
  - Raspberry Pi OS (Raspbian) with Python 3 installed.
  - macOS with Python 3 installed.

---

### **3. Hardware Setup**

1. **Connect the ST7789 LCD to the Raspberry Pi**:
   Use the following GPIO pins:

   | LCD Pin   | Raspberry Pi Pin |
   |-----------|------------------|
   | VCC       | 5V               |
   | GND       | GND              |
   | DIN       | GPIO 19 (MOSI)   |
   | CLK       | GPIO 23 (SCLK)   |
   | CS        | GPIO 24 (CE0)    |
   | DS/DC     | GPIO 25          |
   | RST       | GPIO 27          |
   | BL        | GPIO 18          |

2. Power up the Raspberry Pi and ensure it is connected to the same network as the Mac.

---

### **4. Software Setup**

#### **On the Raspberry Pi**
1. **Update the System**:
   ```bash
   sudo apt update
   sudo apt upgrade
   ```

2. **Install Required Libraries**:
   ```bash
   sudo apt install python3 python3-pip
   pip3 install pillow
   ```

3. **Manufacturer’s Display Library**:


   - The repo contains a folder called `lib`, this contains Waveshare's display library and is referenced in the `screen_stream.py` script. Ensure the lib folder is present next to the `screen_stream.py` script before running.
   - In the `screen_stream.py` script, `from lib import LCD_1inch54` points towards the 1.54 inch display library, this can be changed to another display size. Look for whats available in the `lib` folder and replace the `LCD_1inch54` value.

5. **Save the Receiver Script**:
   Create a new file called `screen_stream.py`:
   ```bash
   screen_stream.py
   ```
   Paste the receiver script from above and save it.

6. **Make the Script Executable**:
   ```bash
   chmod +x screen_stream.py
   ```

---

#### **On the Mac**
1. **Install Python 3**:
   - macOS includes Python 3, but ensure it’s the latest version. Install it using [Homebrew](https://brew.sh) if necessary:
     ```bash
     brew install python
     ```

2. **Install Required Libraries**:
   ```bash
   pip3 install pillow mss
   ```

3. **Save the Sender Script**:
   Create a new file called `screen_capture.py`:
   ```bash
   screen_capture.py
   ```
   Paste the sender script from above and save it.

4. **Make the Script Executable**:
   ```bash
   chmod +x screen_capture.py
   ```

---

### **5. Running the Scripts**

#### Step 1: Start the Receiver on the Raspberry Pi
1. Open a terminal on the Pi.
2. Run the receiver script:
   ```bash
   python3 screen_stream.py
   ```
    or if you run into permission errors:
  
   ```bash
   sudo python3 screen_stream.py
   ```
   The screen will turn white whilst it waits for data

#### Step 2: Start the Sender on the Mac
1. Open a terminal on the Mac.
2. Run the sender script:
   ```bash
   python3 screen_capture.py --host 192.168.86.49 --top 114 --left 340 --width 242 --height 242 --timesleep 0.03 --quality 60
   ```
   Note:
   - Replace the host ip address with your Raspberry Pi’s IP address
   - `top` and `left` define the origin of the capture region in pixels
   - `width` and `height` define the size of the capture region in pixels. 2px added for margin.
   - `timesleep` adjusts the refresh rate (lower is higher refresh rate)
   - `quality` adjust the image quality (0-100)

#### Step 3: Observe the Output
The selected portion of the Mac’s screen will be mirrored on the Pi’s LCD.

---

### **6. Troubleshooting**

1. **Screen Not Updating**:
   - Ensure both scripts are running and connected.
   - Check the network connection between the Mac and Pi.

2. **Image is Truncated or Corrupted**:
   - Ensure the Mac script sends complete images.
   - Increase the delay (`time.sleep`) in the Mac script if needed.

3. **Scripts Not Connecting**:
   - Verify the Pi’s IP address using:
     ```bash
     hostname -I
     ```
   - Ensure both devices are on the same network.

4. **Libraries Not Found**:
   - Reinstall the missing libraries using `pip3`.

---

### **7. Optimizations**

1. **Resolution**:
   - Adjust the capture region in the Mac script for a smaller area.

2. **Frame Rate**:
   - Adjust `time.sleep` in the Mac script to improve refresh rates.

3. **Compression**:
   - Modify the JPEG quality in the Mac script for faster transmission.

---

This setup allows you to mirror a portion of your Mac’s screen to a Raspberry Pi with a 240x240 ST7789 display. Let me know if you need additional details or have any issues!
