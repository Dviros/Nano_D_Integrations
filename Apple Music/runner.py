import serial
import threading
import time
import subprocess
import os
import glob
import json
import queue
import logging
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import esptool

logging.basicConfig(filename='error_log.txt', level=logging.ERROR, format='%(asctime)s %(message)s')

# Load profile from profile.json
def load_profile():
    with open('profile.json') as f:
        return json.load(f)

profile = load_profile()

def find_serial_device():
    devices = glob.glob('/dev/tty.*')
    print(f"Found devices: {devices}")
    devices = [device for device in devices if 'Bluetooth-Incoming-Port' not in device]
    print(f"Filtered devices: {devices}")
    for device in devices:
        if 'usbmodemNano_D1' in device:
            print(f"Selected device: {device}")
            return device
    if devices:
        for device in devices:
            if 'tty.usbmodem' in device:
                print(f"Device detected as tty.usbmodem, running esptool command")
                try:
                    esptool.main(['--port', device, '--trace', 'read_flash', '0x00000', '0x400000', 'firmware_dump.bin'])
                except Exception as e:
                    print(f"Error running esptool: {e}")
                return device
        print(f"Selected default device: {devices[0]}")
        return devices[0]
    return None

def set_volume(volume_level):
    print(f"Setting volume to {volume_level}")
    os.system(f"osascript -e 'set volume output volume {volume_level}'")

def mute_system_audio():
    print("Muting system audio")
    subprocess.run(["osascript", "-e", "set volume with output muted"])

def unmute_system_audio():
    print("Unmuting system audio")
    subprocess.run(["osascript", "-e", "set volume without output muted"])

def get_volume():
    result = subprocess.run(["osascript", "-e", "output volume of (get volume settings)"], capture_output=True, text=True)
    volume_level = int(result.stdout.strip())
    print(f"Current volume: {volume_level}")
    return volume_level

def get_mute_status():
    result = subprocess.run(["osascript", "-e", "output muted of (get volume settings)"], capture_output=True, text=True)
    mute_status = result.stdout.strip() == "true"
    print(f"Current mute status: {mute_status}")
    return mute_status

def sync_device_status():
    volume_level = get_volume()
    mute_status = get_mute_status()
    print(f"Syncing device status - Volume: {volume_level}, Mute: {mute_status}")
    sync_message = json.dumps({"volume": volume_level, "mute": mute_status})
    ser.write(f'{sync_message}\n'.encode())

def log_error(message):
    logging.error(message)

def handle_serial_input(serial_queue):
    while True:
        try:
            if ser.in_waiting > 0:
                data = ser.readline().decode().strip()
                print(f"Received data: {data}")
                serial_queue.put(data)
        except Exception as e:
            log_error(f"Error handling serial input: {e}")

def process_key_press(parsed_data):
    try:
        for command in profile["commands"]:
            if parsed_data["ks"] == command["ks"] and parsed_data["kd"] == command["kd"]:
                print(f"{command['description']}")
                os.system(command["command"])
                break
    except Exception as e:
        log_error(f"Error processing key press: {e}")

def process_volume_change(volume_level):
    try:
        if isinstance(volume_level, int) and 0 <= volume_level <= 100:
            set_volume(volume_level)
    except Exception as e:
        log_error(f"Error processing volume change: {e}")

def process_message(data, volume_queue):
    try:
        parsed_data = json.loads(data)
        if "ks" in parsed_data:
            process_key_press(parsed_data)
        elif "p" in parsed_data:
            volume_queue.append(parsed_data["p"])
        else:
            print("Received unhandled data:", parsed_data)
    except json.JSONDecodeError as e:
        log_error(f"JSON decode error: {data} - {e}")
    except Exception as e:
        log_error(f"Error processing data: {data} - {e}")

def process_serial_queue(serial_queue, volume_queue):
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        while True:
            try:
                data = serial_queue.get()
                future = executor.submit(process_message, data, volume_queue)
                futures.append(future)
                # Clean up completed futures
                futures = [f for f in futures if not f.done()]
            except Exception as e:
                log_error(f"Error processing serial queue: {e}")

def handle_volume_changes(volume_queue):
    last_volume = None
    while True:
        try:
            if volume_queue:
                current_volume = volume_queue[-1]
                if current_volume != last_volume:
                    time.sleep(0.1)  # Small delay to wait for high-speed changes to settle
                    current_volume = volume_queue[-1]  # Get the latest value after delay
                    process_volume_change(current_volume)
                    last_volume = current_volume
                volume_queue.clear()  # Clear the queue to process only the latest value
        except Exception as e:
            log_error(f"Error handling volume changes: {e}")

def terminate_script():
    log_error("No device found")
    print("No device found. Terminating script.")
    exit(1)

def monitor_device():
    while True:
        device = find_serial_device()
        if not device:
            terminate_script()
        time.sleep(10)

def main():
    start_time = time.time()
    while True:
        device = find_serial_device()
        if not device:
            if time.time() - start_time > 10:
                terminate_script()
            time.sleep(1)
            continue

        global ser
        try:
            print(f"Connecting to serial device: {device}")
            ser = serial.Serial(device, 921600)
            time.sleep(2)  # Give some time for the connection to establish
            sync_device_status()  # Sync initial status immediately

            serial_queue = queue.Queue()
            volume_queue = deque(maxlen=100)  # Use deque for volume changes with a larger maximum length

            serial_thread = threading.Thread(target=handle_serial_input, args=(serial_queue,))
            serial_thread.daemon = True
            serial_thread.start()

            processing_thread = threading.Thread(target=process_serial_queue, args=(serial_queue, volume_queue,))
            processing_thread.daemon = True
            processing_thread.start()

            volume_thread = threading.Thread(target=handle_volume_changes, args=(volume_queue,))
            volume_thread.daemon = True
            volume_thread.start()

            monitor_thread = threading.Thread(target=monitor_device)
            monitor_thread.daemon = True
            monitor_thread.start()

            while True:
                if not ser.is_open:
                    terminate_script()
                time.sleep(1)
        except Exception as e:
            log_error(f"Error initializing serial connection: {e}")
            time.sleep(5)  # Wait before trying again

if __name__ == "__main__":
    main()
