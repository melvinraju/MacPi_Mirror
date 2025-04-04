# MacPi Mirror

MacPi Mirror captures your Mac screen and sends it to a Raspberry Pi. The Raspberry Pi receives the data and displays it on a LCD.

- **Hardware**:
  - Raspberry Pi.
  - An SPI LCD.
  - A reliable network connection (Wi-Fi or Ethernet).

- **Software**:
  - Raspberry Pi OS (Raspbian) with Python 3 installed.
  - macOS with Python 3 installed.

---


### **Pi Setup (20 mins)** 
#### **Pi Hardware**
1. **Connect the LCD to the Raspberry Pi**:
   <details>
    <summary>SPI display pinout</summary>

   | LCD Pin   | Raspberry Pi Pin |
   |-----------|------------------|
   | VCC       | 5V               |
   | GND       | GND              |
   | DIN/MOSI  | GPIO 19 (MOSI)   |
   | CLK/SCK   | GPIO 23 (SCLK)   |
   | CS        | GPIO 24 (CE0)    |
   | DS/DC     | GPIO 25          |
   | RST (optional)       | GPIO 27          |
   | BL        | GPIO 18          |
  

   </details>

2. Power up the Raspberry Pi and ensure it is connected to the same network as the Mac.



#### **Pi Software**
1. **Save the Repo Folder Locally**:
   - Save the MacPi Mirror repo folder in your desired location (the folder must contain `screen_stream.py` and the folder `lib`). Note down the file path.
2. **Raspberry Pi Hostname**:

   The scripts find your Pi's IP address by pinging its hostname, by default this is `raspberrypi`. If you have multiple Pis on your network, ensure your Raspberry Pi has a unique hostname, or the script may not stream to the correct Pi.

3. **Enable & Install Required Libraries**:
   Some of the following libraries may already be installed on Pi.
   <details>
     <Summary>SPI</Summary>

     Step 1: Enable SPI on the Raspberry Pi

     Open the terminal and run:
      ```bash
      sudo raspi-config
      ```
      
     Navigate to: Interfacing Options -> SPI -> Enable
      
      Reboot the Pi to apply the changes:
      ```bash
      sudo reboot
      ```
      Step 2: Install spidev Library (optional)
      
      After rebooting, ensure the spidev Python library is installed.
      ```bash
      sudo apt update
      sudo apt install python3-spidev
      ```
      
      If the above does not work, install it using pip:
      ```bash
      pip3 install spidev
      ```

   </details>
   
   <details>
     <Summary>Pillow</Summary>
     
   ```bash
   sudo apt install python3 python3-pip
   pip3 install pillow
   ```
   </details>


4. **Manufacturer’s Display Library**:
   - In the `screen_stream.py` script, adjust the code on lines 9 & 13 to point towards the library with the correct size display (eg. `LCD_1inch54`). Look for available sizes in the `lib` folder.


5. Open a terminal on the Pi and navigate to the location of the `screen_stream.py` script.

6. Run the script:
   ```bash
   python3 screen_stream.py
   ```
   
   The screen will display the Raspberry Pi's hostname and "Waitng for connection..." if successful


   <details>
    <summary>Optional: Make script start in terminal on boot (10 mins)</summary>
    
    
    1. Create the autostart directory if it doesn’t exist:
    ```
    mkdir -p ~/.config/autostart
    ```
    
    2. Create file using nano:
    ```
    nano ~/.config/autostart/start_screen_stream.desktop
    ```
    3. Add the following content, edit the file path if required. Save and exit:
    ```
    [Desktop Entry]
    Type=Application
    Name=Start Screen Stream
    Exec=lxterminal -e "bash -c 'sleep 5; python3 /home/raspberrypi/Desktop/MacPi_Mirror-main/screen_stream.py'"
    X-GNOME-Autostart-enabled=true
    Comment=Delays 5 seconds, then runs screen_stream.py
    ```
    4. Reboot. Terminal will open and run the script after 5 seconds
  
    
     </details>


---


### **Mac Setup (10 mins)**
1. **Save the Repo Folder Locally**:
   - Save the MacPi Mirror repo folder in your desired location (the folder must contain `screen_capture.py`). Note down the file path.
2. **Install Required Libraries**:

    Open terminal on mac and enter the following command:
     ```bash
     pip3 install pillow mss
     ```
3. Open a terminal on the Mac and navigate to the location of the `screen_capture.py` script.
4. Adjust the following script with the configuration guide below and run in terminal:
   ```bash
   python3 screen_capture.py --host raspberrypi  --top 120 --left 1480 --width 242 --height 242 --target-width 240 --target-height 240 --framerate 100 --quality 100 --rotation 0
   ```
   
   Configuration:
   - `host` is your Raspberry Pi's hostname
   - `top` and `left` define the origin of the capture region in pixels
   - `width` and `height` define the size of the capture region in pixels. 2px added for margin.
   - `target-width` and `target-height` is the size of the LCD in pixels
   - `framerate` adjusts the image frame rate
   - `quality` adjust the image quality (0-100)
   - `rotation` defines the rotation the image is displayed (`0`,`90`,`180`,`270`)

The selected portion of the Mac’s screen will be mirrored on the Pi’s LCD.






