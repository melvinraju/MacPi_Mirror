# MacPi Mirror

Macpi Mirror captures a portion of your Mac screen and sends it to a Raspberry Pi. The Raspberry Pi receives the data and displays it on a LCD.

- **Hardware**:
  - Raspberry Pi (any model with GPIO and networking capabilities).
  - ST7789 LCD (1.54" 240x240 is used in this demo).
  - A reliable network connection (Wi-Fi or Ethernet).

- **Software**:
  - Raspberry Pi OS (Raspbian) with Python 3 installed.
  - macOS with Python 3 installed.
  - The scripts use the **Pillow**, **mss**, and **sockets** libraries for capturing, compressing, and transmitting images.

---


### **1. Hardware Setup (10 mins)** 

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


### **2. Software Setup (10 mins)**

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

5. **Save the Receiver Script and Screen Libraries**:
   - Save the script called `screen_stream.py` and folder `lib` in a folder in your desired location. Note down the file path.

6. **Make the Script Executable**:
   Locate the script location in terminal and make the script executable:
   ```bash
   chmod +x screen_stream.py
   ```



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
   - Save the script called `screen_capture.py` in a folder in your desired location. Note down the file path.

5. **Make the Script Executable**:
   Locate the script location in terminal and make the script executable:
   ```bash
   chmod +x screen_capture.py
   ```

---


### **3. Running the Scripts (2 mins)**

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
   python3 screen_capture.py --host 192.168.86.49 --top 100 --left 1480 --width 242 --height 242 --target-width 240 --target-height 240 --timesleep 0.05 --quality 80 --rotation 90
   ```
   Configuration:
   - Replace the host ip address with your Raspberry Pi’s IP address
   - `top` and `left` define the origin of the capture region in pixels
   - `width` and `height` define the size of the capture region in pixels. 2px added for margin.
   - `target-width` and `target-height` is the size of the LCD in pixels
   - `timesleep` adjusts the refresh rate (lower is higher refresh rate)
   - `quality` adjust the image quality (0-100)
   - `rotation` defines the rotation the image is displayed (`0`,`90`,`180`,`270`)

#### Step 3: Observe the Output
The selected portion of the Mac’s screen will be mirrored on the Pi’s LCD.

---

### **Troubleshooting**

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




