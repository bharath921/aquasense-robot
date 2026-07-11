# ESP8266 Driver Installation Guide

## For Windows:

### CH340 Driver (Most Common):
1. Download from: https://sparks.gogo.co.nz/ch340.html
2. Install the driver
3. Restart computer
4. Check Device Manager for "USB-SERIAL CH340"

### CP2102 Driver (Alternative):
1. Download from: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
2. Install for your Windows version
3. Restart computer

## Quick Checks:
1. Device Manager → Ports (COM & LPT)
   - Should show: "Silicon Labs CP210x USB to UART Bridge (COM#)"
   - Or: "USB-SERIAL CH340 (COM#)"

2. If you see "Unknown Device" or yellow warning:
   - Right-click → Update Driver
   - Browse and select downloaded driver

## Arduino IDE Settings:
- Board: "NodeMCU 1.0 (ESP-12E Module)"
- Port: Select the COM port that appears
- Upload Speed: Try 115200, if fails use 9600
- Programmer: "AVRISP mkII"