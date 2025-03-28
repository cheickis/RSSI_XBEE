# send_packet.py
"""
Author: Cheick Ismael MAIGA
Continuously sends a packet from R&D1 to R&D2.
"""

import serial
import time

PORT = 'COM8'  # R&D1 port
BAUD_RATE = 9600
DEST_ADDR = b'\x00\x13\xA2\x00\x42\x6E\xE7\x77'  # MAC of R&D2

def send_unicast_packet(ser):
    # This is a simple example — you can send API frame if in API mode
    ser.write(b'Hello from R&D1\r')
    print("Sent: Hello from R&D1")

def main():
    with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
        print(f"Sending on {PORT}...")
        while True:
            send_unicast_packet(ser)
            time.sleep(5)  # Send every 5 seconds

if __name__ == "__main__":
    main()
