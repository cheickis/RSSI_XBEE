# Author: Cheick (Full Version with Live Graph, Stats, and Auto Save)

import serial
import time
import threading
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from serial.tools import list_ports
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from scripts.xbee_rssi import wait_for_packet, enter_command_mode, exit_command_mode

# === COMMON CONFIG ===
BAUD_RATE = 9600
CSV_FILENAME = 'rssi_log.csv'
stop_event = threading.Event()
rssi_values = []  # Store RSSI history

# === Helper Functions ===

def find_serial_port():
    ports = list_ports.comports()
    candidates = [port.device for port in ports if 'USB' in port.description or 'XBee' in port.description or 'CP210' in port.description]
    if not candidates:
        raise Exception("No suitable serial port found. Please connect the receiver module.")
    if len(candidates) == 1:
        print(f"[Auto] Found serial port: {candidates[0]}")
        return candidates[0]
    else:
        print("[Auto] Multiple serial ports found:")
        for i, device in enumerate(candidates):
            print(f"{i+1}: {device}")
        idx = int(input("Select port number: ")) - 1
        return candidates[idx]

def log_rssi_to_csv(rssi_value):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILENAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, rssi_value])

def update_graph(ax, canvas):
    ax.clear()
    ax.set_title("Live RSSI over Time")
    ax.set_xlabel("Packet #")
    ax.set_ylabel("RSSI (dBm)")
    ax.grid(True)

    if len(rssi_values) >= 2:
        x = np.arange(len(rssi_values))
        y = np.array(rssi_values)

        for i in range(len(x) - 1):
            color = "green" if y[i] > -70 else "orange" if y[i] > -85 else "red"
            ax.plot(x[i:i+2], y[i:i+2], color=color, linewidth=2)

    elif rssi_values:
        ax.plot([0], [rssi_values[0]], marker='o')

    ax.relim()
    ax.autoscale_view()
    canvas.draw()

def update_stats(stats_label):
    if rssi_values:
        avg = sum(rssi_values) / len(rssi_values)
        minimum = min(rssi_values)
        maximum = max(rssi_values)
        stats_label.config(text=f"Avg: {avg:.1f} dBm | Min: {minimum} dBm | Max: {maximum} dBm")
    else:
        stats_label.config(text="No Data Yet")

def read_rssi_loop(label, stats_label, ax, canvas, port_recv):
    try:
        with serial.Serial(port_recv, BAUD_RATE, timeout=1) as ser:
            print(f"[Receiver] Listening on {port_recv}")
            while not stop_event.is_set():
                if wait_for_packet(ser):
                    if enter_command_mode(ser):
                        ser.write(b'ATDB\r')
                        ser.flush()
                        time.sleep(0.2)
                        rssi_hex = ser.read(10).decode(errors='ignore').strip()
                        try:
                            rssi = -int(rssi_hex, 16)
                            print(f"[Receiver] RSSI: {rssi} dBm")
                            rssi_values.append(rssi)
                            if len(rssi_values) > 100:
                                rssi_values.pop(0)  # Keep max 100 points

                            label.config(text=f"{rssi} dBm", fg="green" if rssi > -70 else "orange" if rssi > -85 else "red")
                            update_stats(stats_label)
                            update_graph(ax, canvas)
                            log_rssi_to_csv(rssi)
                        except ValueError:
                            print("[Receiver] Invalid RSSI format:", rssi_hex)
                        exit_command_mode(ser)
                time.sleep(0.1)
    except serial.SerialException as e:
        print(f"[Receiver] Serial error: {e}")
        label.config(text="Serial Error", fg="red")

def save_graph_loop(fig):
    while not stop_event.is_set():
        time.sleep(300)  # Every 5 minutes
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rssi_graph_{timestamp}.png"
        fig.savefig(filename)
        print(f"[AutoSave] Graph saved as {filename}")

def launch_receiver_gui(port_recv):
    root = tk.Tk()
    root.title("Centre for Smart Mining Receiver - RSSI Monitor with Graph")

    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    label = tk.Label(frame, text="Waiting...", font=("Arial", 48), fg="green")
    label.pack(padx=20, pady=20)

    stats_label = tk.Label(frame, text="Avg: -- | Min: -- | Max: --", font=("Arial", 16))
    stats_label.pack(padx=10, pady=10)

    fig, ax = plt.subplots(figsize=(6, 3))
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    receiver_thread = threading.Thread(target=read_rssi_loop, args=(label, stats_label, ax, canvas, port_recv), daemon=True)
    receiver_thread.start()

    saver_thread = threading.Thread(target=save_graph_loop, args=(fig,), daemon=True)
    saver_thread.start()

    def on_close():
        stop_event.set()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

def main_receiver():
    try:
        with open(CSV_FILENAME, 'x', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'RSSI (dBm)'])
    except FileExistsError:
        pass

    port_recv = find_serial_port()
    launch_receiver_gui(port_recv)

# === Entry Point ===
if __name__ == "__main__":
    main_receiver()
