# Author: Cheick
import serial
import time
import threading

from scripts.xbee_rssi import wait_for_packet, enter_command_mode, exit_command_mode

PORT_SEND = 'COM8'  # R&D1
PORT_RECV = 'COM7'  # R&D2
BAUD_RATE = 9600

DEST_ADDR_64 = [0x00, 0x13, 0xA2, 0x00, 0x42, 0x6E, 0xE7, 0x77]  # R&D2 64-bit MAC

def calc_checksum(frame_data):
    return 0xFF - (sum(frame_data) & 0xFF)

def build_api_frame(payload: bytes) -> bytes:
    frame_data = bytearray([
        0x10,       # Frame Type: Transmit Request
        0x01        # Frame ID
    ])
    frame_data.extend(DEST_ADDR_64)   # 64-bit destination address
    frame_data.extend([0xFF, 0xFE])   # 16-bit address unknown
    frame_data.append(0x00)           # Broadcast radius
    frame_data.append(0x00)           # Options
    frame_data.extend(payload)        # Payload

    length = len(frame_data)
    frame = bytearray([0x7E, (length >> 8) & 0xFF, length & 0xFF])
    frame.extend(frame_data)
    frame.append(calc_checksum(frame_data))
    return frame

def send_loop():
    with serial.Serial(PORT_SEND, BAUD_RATE, timeout=1) as ser:
        print("[Sender] Ready to send...")
        while True:
            payload = b'Test'
            api_frame = build_api_frame(payload)
            ser.write(api_frame)
            print("[Sender] Sent API frame:", api_frame.hex())
            time.sleep(5)

def read_rssi_loop():
    with serial.Serial(PORT_RECV, BAUD_RATE, timeout=1) as ser:
        print("[Receiver] Listening on", PORT_RECV)
        while True:
            if wait_for_packet(ser):
                if enter_command_mode(ser):
                    ser.write(b'ATDB\r')
                    time.sleep(0.5)
                    rssi_hex = ser.read(10).decode(errors='ignore').strip()
                    try:
                        rssi = -int(rssi_hex, 16)
                        print(f"[Receiver] RSSI: {rssi} dBm")
                    except ValueError:
                        print("[Receiver] Invalid RSSI format:", rssi_hex)
                    exit_command_mode(ser)
            time.sleep(0.1)

def main():
    sender = threading.Thread(target=send_loop, daemon=True)
    receiver = threading.Thread(target=read_rssi_loop, daemon=True)

    #sender.start()
    receiver.start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
