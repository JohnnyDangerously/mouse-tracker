from pynput import mouse
import keyboard
import time
import csv
import os

# Settings
OUTPUT_FILE = os.path.expanduser("~/Documents/MouseLogs/mouse_log.csv")
HOTKEY_START = "ctrl+alt+1"
HOTKEY_STOP = "ctrl+alt+2"
HOTKEY_QUIT = "ctrl+alt+q"

# Globals
recording = False
log_data = []

def log_event(event_type, x, y, button=None, pressed=None):
    timestamp = time.time()
    log_data.append({
        "time": timestamp,
        "event": event_type,
        "x": x,
        "y": y,
        "button": str(button) if button else "",
        "pressed": pressed if pressed is not None else ""
    })

def on_move(x, y):
    if recording:
        log_event("move", x, y)

def on_click(x, y, button, pressed):
    if recording:
        log_event("click", x, y, button, pressed)

def save_log():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["time", "event", "x", "y", "button", "pressed"])
        writer.writeheader()
        for entry in log_data:
            writer.writerow(entry)

def start_recording():
    global recording
    if not recording:
        recording = True
        print("Started recording.")
    else:
        print("Already recording.")

def stop_recording():
    global recording
    if recording:
        recording = False
        save_log()
        print(f"Stopped recording. Saved data to {OUTPUT_FILE}")
    else:
        print("Not currently recording.")

def quit_app():
    global recording
    if recording:
        save_log()
        print(f"Saved data to {OUTPUT_FILE}")
    print("Exiting application...")
    os._exit(0)

def listen_for_hotkey():
    print(f"Press {HOTKEY_START} to start recording")
    print(f"Press {HOTKEY_STOP} to stop recording and save")
    print(f"Press {HOTKEY_QUIT} to quit the application")
    keyboard.add_hotkey(HOTKEY_START, start_recording)
    keyboard.add_hotkey(HOTKEY_STOP, stop_recording)
    keyboard.add_hotkey(HOTKEY_QUIT, quit_app)
    keyboard.wait()  # waits indefinitely

def start_mouse_listener():
    with mouse.Listener(on_move=on_move, on_click=on_click) as listener:
        listen_for_hotkey()
        listener.join()

if __name__ == "__main__":
    start_mouse_listener()