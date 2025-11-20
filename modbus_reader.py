import os
import csv
import json
import time
import struct
from datetime import datetime
from pymodbus.client import ModbusTcpClient

CONFIG_FILE = "devices.json"
LOG_FOLDER = "logs"

# Ensure logs folder exists
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

# --- JSON Storage ---
def load_devices():
    if not os.path.exists(CONFIG_FILE):
        return []
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_devices(devices):
    with open(CONFIG_FILE, "w") as f:
        json.dump(devices, f, indent=4)

# --- CSV Logging ---
def csv_filename(ip, port):
    safe_ip = ip.replace(".", "_")
    return os.path.join(LOG_FOLDER, f"{safe_ip}_{port}.csv")

def write_csv(ip, port, reg, value):
    filename = csv_filename(ip, port)
    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "IP", "Port", "Register", "Value"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ip, port, reg, value
        ])

# --- Modbus Reading ---
def read_modbus_device(host, port, registers):
    client = ModbusTcpClient(host=host, port=port, timeout=3)
    if not client.connect():
        return f"[{host}] Connection Failed ❌"
    output = f"[{host}] Connected ✔\n"
    for reg in registers:
        try:
            result = client.read_input_registers(address=reg, count=2)
            if result.isError():
                output += f"[{host}] Read Error @ {reg}: {result}\n"
                continue
            h, l = result.registers
            raw = struct.pack(">HH", h, l)
            float_val = struct.unpack(">f", raw)[0]
            output += f"[{host}] Reg {reg} → {float_val}\n"
            write_csv(host, port, reg, float_val)
        except Exception as e:
            output += f"[{host}] Error: {e}\n"
    client.close()
    output += f"[{host}] Disconnected\n"
    return output
