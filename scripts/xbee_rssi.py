"""
Author: Cheick
Description: Continuously listen for unicast packets on XBee R&D2 and display RSSI after each.
"""

import serial
import time

PORT = 'COM7'       # Replace with the serial port connected to R&D2
BAUD_RATE = 9600

def enter_command_mode(ser):
    """Enter AT command mode."""
    ser.write(b'+++')
    time.sleep(1)
    response = ser.read(10)
    return b'OK' in response

def exit_command_mode(ser):
    """Exit AT command mode."""
    ser.write(b'ATCN\r')
    time.sleep(0.5)
    ser.read(10)

def wait_for_packet(ser, timeout_sec=10):
    """Wait for incoming packet for a set duration."""
    print("Waiting for incoming packet...")
    timeout = time.time() + timeout_sec
    while time.time() < timeout:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            print("Packet received:", data.decode(errors='ignore').strip())
            return True
        time.sleep(0.1)
    print("No packet received.")
    return False

def read_rssi(ser):
    """Send ATDB and return RSSI value in dBm."""
    if enter_command_mode(ser):
        print("Entered command mode.")
        ser.write(b'ATDB\r')
        time.sleep(0.5)
        rssi_hex = ser.read(10).decode(errors='ignore').strip()
        try:
            rssi = -int(rssi_hex, 16)
            print(f"RSSI: {rssi} dBm")
            return rssi
        except ValueError:
            print("Invalid RSSI format:", rssi_hex)
    else:
        print("Failed to enter command mode.")
    return None

def monitor_rssi():
    """Main loop to continuously check for incoming packets and get RSSI."""
    with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
        print(f"Listening on {PORT}...")
        while True:
            if wait_for_packet(ser):
                read_rssi(ser)
                exit_command_mode(ser)
            else:
                print("Waiting again...")
            print("-" * 40)
            time.sleep(1)

def main():
    monitor_rssi()

if __name__ == "__main__":
    main()
