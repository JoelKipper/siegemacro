import ctypes
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk
from ctypes import wintypes
import os
import configparser
import json

from pynput import keyboard, mouse

# ==============================
# SETTINGS (DPI speichern)
# ==============================

SETTINGS_FILE = "settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"dpi": 800}

    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"dpi": 800}


def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except:
        pass


# ==============================
# CONFIG AUSLESEN (R6)
# ==============================

def load_r6_config():
    try:
        documents = os.path.join(os.path.expanduser("~"), "Documents")
        base_path = os.path.join(documents, "My Games", "Rainbow Six - Siege")

        if not os.path.exists(base_path):
            return None

        for folder in os.listdir(base_path):
            full_path = os.path.join(base_path, folder)
            if not os.path.isdir(full_path):
                continue

            config_path = os.path.join(full_path, "GameSettings.ini")

            if not os.path.exists(config_path):
                continue

            config = configparser.ConfigParser()
            config.read(config_path)

            if "INPUT" not in config:
                continue

            sec = config["INPUT"]

            sens = float(sec.get("MouseSensitivity", 30))
            sens_mult = float(sec.get("MouseSensitivityMultiplierUnit", 0.002))
            ads = float(sec.get("ADSMouseSensitivityGlobal", 40))
            ads_mult = float(sec.get("ADSMouseMultiplierUnit", 0.02))

            return sens, sens_mult, ads, ads_mult

        return None

    except Exception as e:
        print("Config Fehler:", e)
        return None


# ==============================
# SPEED BERECHNUNG
# ==============================

def calc_speed_from_config(dpi, slider_value):
    data = load_r6_config()
    if not data:
        return slider_value

    sens, sens_mult, ads, ads_mult = data

    base = sens * sens_mult
    ads_val = ads * ads_mult

    base_speed = dpi * base * ads_val

    slider_multiplier = slider_value / 100.0

    return base_speed * slider_multiplier


# ==============================
# WINDOWS INPUT
# ==============================

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    )


class INPUT(ctypes.Structure):
    _fields_ = (
        ("type", wintypes.DWORD),
        ("mi", MOUSEINPUT),
    )


_user32 = ctypes.WinDLL("user32", use_last_error=True)


def win_send_mouse_relative(dx: int, dy: int) -> bool:
    extra = wintypes.ULONG(0)
    mi = MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
    inp = INPUT(INPUT_MOUSE, mi)
    return _user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT)) == 1


# ==============================
# APP
# ==============================

class MacroApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Click Move Down")
        self.root.resizable(False, False)

        # Settings laden
        self.settings = load_settings()

        self.enabled_var = tk.BooleanVar(value=False)
        self.speed_var = tk.IntVar(value=100)
        self.dpi_var = tk.IntVar(value=self.settings.get("dpi", 800))
        self.status_var = tk.StringVar()

        self._mouse_controller = mouse.Controller()

        self._left_down = False
        self._right_down = False
        self._accum_y = 0.0

        self._state_lock = threading.Lock()
        self._macro_enabled = False
        self._macro_speed = 0

        self._stop_smooth = threading.Event()
        self._smooth_thread = threading.Thread(target=self._smooth_drag_loop, daemon=True)

        self._build_ui()
        self._set_status()
        self._smooth_thread.start()
        self._start_listeners()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=14)
        frame.grid(row=0, column=0, sticky="nsew")

        title = ttk.Label(frame, text="Maus flüssig nach unten (L+R halten)", font=("Segoe UI", 11, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        enabled = ttk.Checkbutton(
            frame,
            text="Aktiviert (Toggle global mit #)",
            variable=self.enabled_var,
            command=self._set_status,
        )
        enabled.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Label(frame, text="Stärke (%):").grid(row=2, column=0, sticky="w")

        slider = ttk.Scale(
            frame,
            from_=10,
            to=1000,
            orient="horizontal",
            command=self._on_slider,
        )
        slider.set(self.speed_var.get())
        slider.grid(row=3, column=0, sticky="ew", pady=(4, 0))

        value = ttk.Label(frame, textvariable=self.speed_var, width=4, anchor="e")
        value.grid(row=3, column=1, sticky="e", padx=(10, 0))

        # 🆕 DPI Feld
        ttk.Label(frame, text="DPI:").grid(row=4, column=0, sticky="w", pady=(10, 0))
        dpi_entry = ttk.Entry(frame, textvariable=self.dpi_var, width=10)
        dpi_entry.grid(row=4, column=1, sticky="e", pady=(10, 0))

        status = ttk.Label(frame, textvariable=self.status_var)
        status.grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 0))

        frame.columnconfigure(0, weight=1)

    def _on_slider(self, val: str) -> None:
        self.speed_var.set(int(float(val)))
        self._set_status()

    def _save_dpi(self):
        self.settings["dpi"] = self.dpi_var.get()
        save_settings(self.settings)

    def _sync_internal_state(self) -> None:
        with self._state_lock:
            self._macro_enabled = self.enabled_var.get()

            dpi = self.dpi_var.get()
            self._macro_speed = calc_speed_from_config(dpi, self.speed_var.get())

    def _set_status(self) -> None:
        self._save_dpi()
        self._sync_internal_state()

        state = "AN" if self.enabled_var.get() else "AUS"
        self.status_var.set(
            f"Status: {state} | Stärke: {self.speed_var.get()}% | DPI: {self.dpi_var.get()} | Speed: {round(self._macro_speed,1)}"
        )

    def _smooth_drag_loop(self) -> None:
        last = time.perf_counter()
        tick = 1.0 / 120.0

        while not self._stop_smooth.wait(timeout=tick):
            now = time.perf_counter()
            dt = min(now - last, 0.05)
            last = now

            with self._state_lock:
                enabled = self._macro_enabled
                speed = float(self._macro_speed)

            if not enabled or not (self._left_down and self._right_down):
                self._accum_y = 0.0
                continue

            self._accum_y += speed * dt
            step = int(self._accum_y)
            self._accum_y -= step

            if step == 0:
                continue

            win_send_mouse_relative(0, step)

    def _toggle_enabled(self) -> None:
        self.enabled_var.set(not self.enabled_var.get())
        self._set_status()

    def _on_key_press(self, key):
        if (hasattr(key, "char") and key.char == "#") or key == keyboard.Key.f8:
            self.root.after(0, self._toggle_enabled)

    def _on_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            self._left_down = pressed
        elif button == mouse.Button.right:
            self._right_down = pressed

        if not pressed:
            self._accum_y = 0.0

    def _start_listeners(self):
        keyboard.Listener(on_press=self._on_key_press).start()
        mouse.Listener(on_click=self._on_click).start()

    def _on_close(self):
        self._stop_smooth.set()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    MacroApp().run()