# Author: Cheick (Headless Sender for Pi Field Deployment)

import serial
import time
import csv
from datetime import datetime
from serial.tools import list_ports

# === CONFIG ===
BAUD_RATE = 9600
DEST_ADDR_64 = [0x00, 0x13, 0xA2, 0x00, 0x42, 0x6E, 0xE7, 0x77]  # R&D2 MAC
CSV_FILENAME = 'tx_log.csv'

def find_serial_port():
    ports = list_ports.comports()
    for port in ports:
        if 'USB' in port.description or 'XBee' in port.description or 'CP210' in port.description:
            print(f"[Auto] Found serial port: {port.device}")
            return port.device
    raise Exception("No suitable serial port found. Please connect the sender module.")

def calc_checksum(frame_data):
    return 0xFF - (sum(frame_data) & 0xFF)

def build_api_frame(payload: bytes) -> bytes:
    frame_data = bytearray([
        0x10,  # Frame Type: Transmit Request
        0x01   # Frame ID
    ])
    frame_data.extend(DEST_ADDR_64)
    frame_data.extend([0xFF, 0xFE])  # 16-bit address unknown
    frame_data.append(0x00)          # Broadcast radius
    frame_data.append(0x00)          # Options
    frame_data.extend(payload)

    length = len(frame_data)
    frame = bytearray([0x7E, (length >> 8) & 0xFF, length & 0xFF])
    frame.extend(frame_data)
    frame.append(calc_checksum(frame_data))
    return frame

def log_transmission(status, frame_hex=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILENAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, status, frame_hex])

def main_sender():
    try:
        with open(CSV_FILENAME, 'x', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Status', 'Frame (Hex)'])
    except FileExistsError:
        pass

    port_send = find_serial_port()

    with serial.Serial(port_send, BAUD_RATE, timeout=1) as ser:
        print(f"[Sender] Ready to send on {port_send}")
        while True:
            payload = b'Test'
            api_frame = build_api_frame(payload)
            try:
                ser.write(api_frame)
                print("[Sender] Sent API frame:", api_frame.hex())
                log_transmission("Success", api_frame.hex())
            except serial.SerialTimeoutException as e:
                print(f"[Sender] Timeout error: {e}")
                log_transmission("Timeout Error", api_frame.hex())
            time.sleep(5)

if __name__ == "__main__":
    main_sender()
