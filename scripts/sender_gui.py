# Author: Cheick
import serial
import time
import threading
import csv
from datetime import datetime
import tkinter as tk

# === COMMON CONFIG ===
PORT_SEND = 'COM8'  # R&D1

BAUD_RATE = 9600


DEST_ADDR_64 = [0x00, 0x13, 0xA2, 0x00, 0x42, 0x6E, 0xE7, 0x77]  # R&D2 MAC

def calc_checksum(frame_data):
    return 0xFF - (sum(frame_data) & 0xFF)

def build_api_frame(payload: bytes) -> bytes:
    frame_data = bytearray([
        0x10,       # Frame Type: Transmit Request
        0x01        # Frame ID
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

# =========================
# SENDER GUI (R&D1 Machine)
# =========================
def send_loop(label):
    with serial.Serial(PORT_SEND, BAUD_RATE, timeout=1) as ser:
        print("[Sender] Ready to send...")
        while True:
            payload = b'Test'
            api_frame = build_api_frame(payload)
            ser.write(api_frame)
            print("[Sender] Sent API frame:", api_frame.hex())
            label.config(text="Sent")
            time.sleep(5)

def launch_sender_gui():
    root = tk.Tk()
    root.title("Sender - XBee R&D1")
    label = tk.Label(root, text="Waiting...", font=("Arial", 48), fg="blue")
    label.pack(padx=40, pady=40)

    sender_thread = threading.Thread(target=send_loop, args=(label,), daemon=True)
    sender_thread.start()

    root.mainloop()

# ============
# ENTRY POINT
# ============
def main_sender():
    launch_sender_gui()



if __name__ == "__main__":
    # Change which to run
     main_sender()

