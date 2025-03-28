# Author: Cheick
import serial
import time
import threading
import csv
from datetime import datetime
import tkinter as tk

# === COMMON CONFIG ===

PORT_RECV = 'COM7'  # R&D2
BAUD_RATE = 9600
CSV_FILENAME = 'rssi_log.csv'

# ===========================
# RECEIVER GUI (R&D2 Machine)
# ===========================
from scripts.xbee_rssi import wait_for_packet, enter_command_mode, exit_command_mode

def log_rssi_to_csv(rssi_value):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILENAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, rssi_value])

def read_rssi_loop(label):
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
                        label.config(text=f"{rssi} dBm")
                        log_rssi_to_csv(rssi)
                    except ValueError:
                        print("[Receiver] Invalid RSSI format:", rssi_hex)
                    exit_command_mode(ser)
            time.sleep(0.1)

def launch_receiver_gui():
    root = tk.Tk()
    root.title("Receiver - RSSI Monitor")
    label = tk.Label(root, text="Waiting...", font=("Arial", 48), fg="green")
    label.pack(padx=40, pady=40)

    receiver_thread = threading.Thread(target=read_rssi_loop, args=(label,), daemon=True)
    receiver_thread.start()

    root.mainloop()



def main_receiver():
    try:
        with open(CSV_FILENAME, 'x', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'RSSI (dBm)'])
    except FileExistsError:
        pass
    launch_receiver_gui()

if __name__ == "__main__":

    main_receiver()
