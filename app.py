import ctypes
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk
from ctypes import wintypes

from pynput import keyboard, mouse

# Windows: echte relative Maus-Deltas per SendInput (wie Hardware), nicht nur Desktop-Cursor.
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


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    )


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    )


class INPUT_UNION(ctypes.Union):
    _fields_ = (
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    )


class INPUT(ctypes.Structure):
    _fields_ = (
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION),
    )


_user32 = ctypes.WinDLL("user32", use_last_error=True)


def win_send_mouse_relative(dx: int, dy: int) -> bool:
    extra = wintypes.ULONG(0)
    mi = MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi = mi
    return _user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT)) == 1


class MacroApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Click Move Down")
        self.root.resizable(False, False)

        self.enabled_var = tk.BooleanVar(value=False)
        self.speed_var = tk.IntVar(value=120)
        self.status_var = tk.StringVar()

        self._mouse_controller = mouse.Controller()
        self._kb_listener: keyboard.Listener | None = None
        self._mouse_listener: mouse.Listener | None = None

        self._left_down = False
        self._right_down = False  # <-- NEU
        self._accum_y = 0.0

        self._state_lock = threading.Lock()
        self._macro_enabled = False
        self._macro_speed = 120

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

        ttk.Label(frame, text="Geschwindigkeit (Pixel/Sekunde):").grid(row=2, column=0, sticky="w")

        slider = ttk.Scale(
            frame,
            from_=10,
            to=800,
            orient="horizontal",
            command=self._on_slider,
        )
        slider.set(self.speed_var.get())
        slider.grid(row=3, column=0, sticky="ew", pady=(4, 0))

        value = ttk.Label(frame, textvariable=self.speed_var, width=4, anchor="e")
        value.grid(row=3, column=1, sticky="e", padx=(10, 0))

        status = ttk.Label(frame, textvariable=self.status_var)
        status.grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))

        frame.columnconfigure(0, weight=1)

    def _on_slider(self, val: str) -> None:
        self.speed_var.set(int(float(val)))
        self._set_status()

    def _sync_internal_state(self) -> None:
        with self._state_lock:
            self._macro_enabled = self.enabled_var.get()
            self._macro_speed = int(self.speed_var.get())

    def _set_status(self) -> None:
        self._sync_internal_state()
        state = "AN" if self.enabled_var.get() else "AUS"
        self.status_var.set(f"Status: {state} | {self.speed_var.get()} px/s | Hotkey: # (Fallback: F8)")

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

            # <-- GEÄNDERT: beide Buttons müssen gedrückt sein
            if not enabled or not (self._left_down and self._right_down):
                self._accum_y = 0.0
                continue

            self._accum_y += speed * dt
            step = int(self._accum_y)
            self._accum_y -= step

            if step == 0:
                continue

            try:
                if sys.platform == "win32":
                    if not win_send_mouse_relative(0, step):
                        self._mouse_controller.move(0, step)
                else:
                    self._mouse_controller.move(0, step)
            except Exception:
                pass

    def _toggle_enabled(self) -> None:
        self.enabled_var.set(not self.enabled_var.get())
        self._set_status()

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        is_hash = isinstance(key, keyboard.KeyCode) and key.char == "#"
        is_fallback = key == keyboard.Key.f8
        if is_hash or is_fallback:
            self.root.after(0, self._toggle_enabled)

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if button == mouse.Button.left:
            self._left_down = bool(pressed)
        elif button == mouse.Button.right:
            self._right_down = bool(pressed)

        if not pressed:
            self._accum_y = 0.0

    def _start_listeners(self) -> None:
        def start_kb() -> None:
            self._kb_listener = keyboard.Listener(on_press=self._on_key_press)
            self._kb_listener.start()

        def start_mouse() -> None:
            self._mouse_listener = mouse.Listener(on_click=self._on_click)
            self._mouse_listener.start()

        threading.Thread(target=start_kb, daemon=True).start()
        threading.Thread(target=start_mouse, daemon=True).start()

    def _on_close(self) -> None:
        self._stop_smooth.set()
        try:
            if self._kb_listener is not None:
                self._kb_listener.stop()
            if self._mouse_listener is not None:
                self._mouse_listener.stop()
        finally:
            self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    MacroApp().run()