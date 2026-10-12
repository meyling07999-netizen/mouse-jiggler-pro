"""
Mouse Jiggler & Auto Mouse Mover — Versi Python (Tkinter GUI)
==============================================================

Fitur:
  1. Mouse Jiggler — gerakkan mouse sedikit secara berkala (anti-sleep/AFK)
     - Pola: linear, circular, zigzag, random, diagonal, figure-8, wave, spiral
  2. Auto Clicker — klik otomatis (kiri/kanan/tengah), single & double click
  3. Auto Actions — buka tab, scroll, refresh, switch app, ketik teks, dll.
  4. Custom Move — gerakkan mouse ke koordinat tertentu
  5. Keyboard Shortcuts — tekan kombinasi tombol keyboard otomatis
  6. Activity Log — log aktivitas real-time di GUI
  7. Status indicator — aktif / mati

Instalasi:
    pip install pyautogui

Cara menjalankan:
    python mouse_jiggler.py
"""

import threading
import time
import random
import math
import platform
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import pyautogui
except ImportError:
    print("PyAutoGUI belum terinstal. Jalankan: pip install pyautogui")
    raise

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

SCREEN_W, SCREEN_H = pyautogui.size()


def is_mac() -> bool:
    return platform.system() == "Darwin"


# ====================================================================== #
#  Worker threads
# ====================================================================== #

class JigglerWorker(threading.Thread):

    def __init__(self, interval: float, distance: int, pattern: str, log_fn=None):
        super().__init__(daemon=True)
        self.interval = interval
        self.distance = distance
        self.pattern = pattern
        self.log_fn = log_fn
        self._stop_flag = threading.Event()

    def stop(self):
        self._stop_flag.set()

    def _log(self, msg: str):
        if self.log_fn:
            self.log_fn(f"[Jiggler] {msg}")

    def run(self):
        self._log(f"Mulai — pola={self.pattern}, interval={self.interval}s, jarak={self.distance}px")
        while not self._stop_flag.is_set():
            try:
                cx, cy = pyautogui.position()
                handler = {
                    "linear": self._linear,
                    "circular": self._circular,
                    "zigzag": self._zigzag,
                    "random": self._random_move,
                    "diagonal": self._diagonal,
                    "figure8": self._figure8,
                    "wave": self._wave,
                    "spiral": self._spiral,
                }.get(self.pattern, self._linear)
                handler(cx, cy)
                self._stop_flag.wait(self.interval)
            except pyautogui.FailSafeException:
                self._log("Failsafe aktif — berhenti darurat")
                break
        self._log("Dihentikan")

    def _linear(self, cx, cy):
        off = random.randint(max(1, self.distance - 1), self.distance + 1)
        pyautogui.moveRel(off, 0, duration=0.25)
        time.sleep(0.1)
        pyautogui.moveRel(-off, 0, duration=0.25)

    def _circular(self, cx, cy):
        r = self.distance + 5
        steps = 12
        for i in range(steps + 1):
            if self._stop_flag.is_set(): return
            angle = 2 * math.pi * i / steps
            px = cx + int(r * math.cos(angle))
            py = cy + int(r * math.sin(angle))
            pyautogui.moveTo(px, py, duration=0.05)

    def _zigzag(self, cx, cy):
        d = self.distance
        for dx, dy in [(d, 0), (0, d), (-d, 0), (0, -d)]:
            if self._stop_flag.is_set(): return
            pyautogui.moveRel(dx, dy, duration=0.2)
            time.sleep(0.05)

    def _random_move(self, cx, cy):
        dx = random.randint(-self.distance, self.distance)
        dy = random.randint(-self.distance, self.distance)
        pyautogui.moveRel(dx, dy, duration=0.25)
        time.sleep(0.1)
        pyautogui.moveRel(-dx, -dy, duration=0.25)

    def _diagonal(self, cx, cy):
        d = self.distance
        pyautogui.moveRel(d, d, duration=0.3)
        time.sleep(0.1)
        pyautogui.moveRel(-d, -d, duration=0.3)

    def _figure8(self, cx, cy):
        r = self.distance + 8
        steps = 20
        for i in range(steps + 1):
            if self._stop_flag.is_set(): return
            t = 2 * math.pi * i / steps
            px = cx + int(r * math.sin(t))
            py = cy + int(r * math.sin(2 * t) // 2)
            pyautogui.moveTo(px, py, duration=0.04)

    def _wave(self, cx, cy):
        d = self.distance
        steps = 10
        for i in range(steps + 1):
            if self._stop_flag.is_set(): return
            offset_x = int(d * 2 * i / steps - d)
            offset_y = int(d * math.sin(math.pi * i / steps * 2))
            pyautogui.moveTo(cx + offset_x, cy + offset_y, duration=0.05)

    def _spiral(self, cx, cy):
        max_r = self.distance + 10
        steps = 24
        for i in range(steps + 1):
            if self._stop_flag.is_set(): return
            angle = 4 * math.pi * i / steps
            r = int(max_r * i / steps)
            px = cx + int(r * math.cos(angle))
            py = cy + int(r * math.sin(angle))
            pyautogui.moveTo(px, py, duration=0.04)


class ClickerWorker(threading.Thread):

    def __init__(self, button: str, interval: float, count: int, double_click: bool, log_fn=None):
        super().__init__(daemon=True)
        self.button = button
        self.interval = interval
        self.count = count
        self.double_click = double_click
        self.log_fn = log_fn
        self._stop_flag = threading.Event()

    def stop(self):
        self._stop_flag.set()

    def _log(self, msg: str):
        if self.log_fn:
            self.log_fn(f"[Clicker] {msg}")

    def run(self):
        self._log(f"Mulai — tombol={self.button}, interval={self.interval}s, double={self.double_click}")
        n = 0
        while not self._stop_flag.is_set():
            try:
                if self.double_click:
                    pyautogui.doubleClick(button=self.button)
                else:
                    pyautogui.click(button=self.button)
                n += 1
                self._log(f"Klik #{n}")
                if self.count > 0 and n >= self.count:
                    self._log(f"Selesai — {n} klik")
                    break
                self._stop_flag.wait(self.interval)
            except pyautogui.FailSafeException:
                self._log("Failsafe aktif — berhenti darurat")
                break
        self._log("Dihentikan")


class ActionWorker(threading.Thread):

    def __init__(self, action: str, interval: float, custom_text: str, log_fn=None):
        super().__init__(daemon=True)
        self.action = action
        self.interval = interval
        self.custom_text = custom_text
        self.log_fn = log_fn
        self._stop_flag = threading.Event()

    def stop(self):
        self._stop_flag.set()

    def _log(self, msg: str):
        if self.log_fn:
            self.log_fn(f"[Action] {msg}")

    def run(self):
        self._log(f"Mulai — aksi={self.action}, interval={self.interval}s")
        while not self._stop_flag.is_set():
            try:
                self._execute()
                self._stop_flag.wait(self.interval)
            except pyautogui.FailSafeException:
                self._log("Failsafe aktif — berhenti darurat")
                break
        self._log("Dihentikan")

    def _execute(self):
        mod = "command" if is_mac() else "ctrl"
        alt_mod = "command" if is_mac() else "alt"
        if self.action == "open_tab":
            pyautogui.hotkey(mod, "t")
            self._log("Buka tab baru")
        elif self.action == "close_tab":
            pyautogui.hotkey(mod, "w")
            self._log("Tutup tab")
        elif self.action == "scroll_down":
            pyautogui.scroll(-300)
            self._log("Scroll ke bawah")
        elif self.action == "scroll_up":
            pyautogui.scroll(300)
            self._log("Scroll ke atas")
        elif self.action == "refresh":
            pyautogui.hotkey(mod, "r")
            self._log("Refresh halaman")
        elif self.action == "switch_app":
            pyautogui.hotkey(alt_mod, "tab")
            self._log("Ganti aplikasi")
        elif self.action == "type_text":
            text = self.custom_text or "KeepActive "
            pyautogui.typewrite(text, interval=0.05)
            self._log(f"Ketik: '{text}'")
        elif self.action == "volume_mute":
            pyautogui.press("volumemute")
            self._log("Toggle mute volume")
        elif self.action == "capslock":
            pyautogui.press("capslock")
            time.sleep(0.2)
            pyautogui.press("capslock")
            self._log("Toggle CapsLock")
        elif self.action == "lock_screen":
            if is_mac():
                pyautogui.hotkey(mod, alt_mod, "q")
            else:
                pyautogui.hotkey(mod, "l") if not is_mac() else None
            self._log("Lock screen (Windows)")
        elif self.action == "screenshot":
            if is_mac():
                pyautogui.hotkey(mod, "shift", "3")
            else:
                pyautogui.hotkey("win", "shift", "s") if not is_mac() else None
            self._log("Screenshot")


class CustomMoveWorker(threading.Thread):
    """Gerakkan mouse ke koordinat tertentu secara berulang atau sekali."""

    def __init__(self, x: int, y: int, repeat: bool, interval: float, log_fn=None):
        super().__init__(daemon=True)
        self.x = x
        self.y = y
        self.repeat = repeat
        self.interval = interval
        self.log_fn = log_fn
        self._stop_flag = threading.Event()

    def stop(self):
        self._stop_flag.set()

    def _log(self, msg: str):
        if self.log_fn:
            self.log_fn(f"[CustomMove] {msg}")

    def run(self):
        self._log(f"Gerak ke ({self.x}, {self.y}) — repeat={self.repeat}")
        while not self._stop_flag.is_set():
            try:
                pyautogui.moveTo(self.x, self.y, duration=0.5)
                self._log(f"Mouse di ({self.x}, {self.y})")
                if not self.repeat:
                    break
                self._stop_flag.wait(self.interval)
            except pyautogui.FailSafeException:
                self._log("Failsafe aktif — berhenti darurat")
                break
        self._log("Dihentikan")


class KeyboardShortcutWorker(threading.Thread):
    """Tekan kombinasi tombol keyboard secara berulang."""

    def __init__(self, keys_str: str, interval: float, log_fn=None):
        super().__init__(daemon=True)
        self.keys_str = keys_str
        self.interval = interval
        self.log_fn = log_fn
        self._stop_flag = threading.Event()

    def stop(self):
        self._stop_flag.set()

    def _log(self, msg: str):
        if self.log_fn:
            self.log_fn(f"[Keyboard] {msg}")

    def run(self):
        keys = [k.strip() for k in self.keys_str.split("+")]
        self._log(f"Mulai — shortcut: {self.keys_str}")
        while not self._stop_flag.is_set():
            try:
                pyautogui.hotkey(*keys)
                self._log(f"Ditekan: {self.keys_str}")
                self._stop_flag.wait(self.interval)
            except pyautogui.FailSafeException:
                self._log("Failsafe aktif — berhenti darurat")
                break
            except Exception as e:
                self._log(f"Error: {e}")
                break
        self._log("Dihentikan")


# ====================================================================== #
#  Main GUI Application
# ====================================================================== #

class MouseJigglerApp:

    BG = "#0f0f1a"
    CARD_BG = "#1c1c2e"
    CARD_HOVER = "#232338"
    ACCENT = "#3b82f6"
    ACCENT_HOVER = "#2563eb"
    SUCCESS = "#22c55e"
    DANGER = "#ef4444"
    WARNING = "#f59e0b"
    TEXT = "#e2e8f0"
    TEXT_MUTED = "#94a3b8"
    ENTRY_BG = "#0a0a12"
    BORDER = "#2e2e44"
    LOG_BG = "#08080f"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Mouse Jiggler & Auto Mover Pro")
        self.root.geometry("720x720")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG)

        self.jiggler_worker: JigglerWorker | None = None
        self.clicker_worker: ClickerWorker | None = None
        self.action_worker: ActionWorker | None = None
        self.custom_worker: CustomMoveWorker | None = None
        self.keyboard_worker: KeyboardShortcutWorker | None = None

        self._build_styles()
        self._build_header()
        self._build_status()
        self._build_tabs()
        self._build_log()

    # --- styles --- #

    def _build_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook", background=self.BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=self.CARD_BG, foreground=self.TEXT_MUTED,
                        padding=(18, 8), font=("Segoe UI", 10))
        style.map("TNotebook.Tab", background=[("selected", self.ACCENT)], foreground=[("selected", "white")])
        style.configure("TFrame", background=self.BG)
        style.configure("TCheckbutton", background=self.CARD_BG, foreground=self.TEXT)

    # --- header --- #

    def _build_header(self):
        frame = tk.Frame(self.root, bg=self.BG)
        frame.pack(fill="x", pady=(16, 4))
        tk.Label(frame, text="Mouse Jiggler & Auto Mover Pro", font=("Segoe UI", 18, "bold"),
                 bg=self.BG, fg=self.TEXT).pack()
        tk.Label(frame, text="Cegah mode sleep / AFK — gerakkan kursor, klik, & keyboard otomatis",
                 font=("Segoe UI", 10), bg=self.BG, fg=self.TEXT_MUTED).pack()

    def _build_status(self):
        frame = tk.Frame(self.root, bg=self.BG)
        frame.pack(fill="x", padx=20, pady=(8, 4))
        self.status_dot = tk.Label(frame, text="\u25cf", font=("Segoe UI", 13), bg=self.BG, fg=self.DANGER)
        self.status_dot.pack(side="left", padx=(0, 6))
        self.status_text = tk.Label(frame, text="Status: MATI", font=("Segoe UI", 11, "bold"),
                                    bg=self.BG, fg=self.DANGER)
        self.status_text.pack(side="left")
        self.pos_label = tk.Label(frame, text="", font=("Segoe UI", 9), bg=self.BG, fg=self.TEXT_MUTED)
        self.pos_label.pack(side="right")
        ttk.Separator(frame).pack(fill="x", side="bottom", pady=(6, 0))
        self._update_pos()

    def _update_pos(self):
        try:
            x, y = pyautogui.position()
            self.pos_label.config(text=f"Mouse: {x}, {y}  |  Layar: {SCREEN_W}x{SCREEN_H}")
        except Exception:
            pass
        self.root.after(200, self._update_pos)

    # --- tabs --- #

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=6)
        self._build_jiggler_tab()
        self._build_clicker_tab()
        self._build_actions_tab()
        self._build_custom_move_tab()
        self._build_keyboard_tab()

    def _make_card(self, parent):
        return tk.Frame(parent, bg=self.CARD_BG, relief="flat", bd=0)

    def _make_label(self, parent, text, font=("Segoe UI", 10)):
        return tk.Label(parent, text=text, font=font, bg=self.CARD_BG, fg=self.TEXT)

    def _make_entry(self, parent, default, width=10):
        e = tk.Entry(parent, width=width, font=("Segoe UI", 11), bg=self.ENTRY_BG, fg=self.TEXT,
                     insertbackground=self.TEXT, relief="flat", justify="center")
        e.insert(0, str(default))
        return e

    def _make_btn(self, parent, text, bg, command, state="normal"):
        return tk.Button(parent, text=text, width=10, bg=bg, fg="white", font=("Segoe UI", 10, "bold"),
                         relief="flat", state=state, activebackground=self.ACCENT_HOVER, command=command)

    def _make_row(self, card, label_text, widget, pady=6):
        row = tk.Frame(card, bg=self.CARD_BG)
        row.pack(fill="x", padx=16, pady=pady)
        self._make_label(row, label_text).pack(side="left")
        widget.pack(side="right")

    def _make_btn_row(self, card, start_cmd, stop_cmd):
        f = tk.Frame(card, bg=self.CARD_BG)
        f.pack(pady=(8, 14))
        start = self._make_btn(f, "Start", self.SUCCESS, start_cmd)
        start.pack(side="left", padx=6)
        stop = self._make_btn(f, "Stop", self.DANGER, stop_cmd, state="disabled")
        stop.pack(side="left", padx=6)
        return start, stop

    # -- Jiggler tab -- #

    def _build_jiggler_tab(self):
        tab = tk.Frame(self.notebook, bg=self.BG)
        self.notebook.add(tab, text=" Jiggler ")
        card = self._make_card(tab)
        card.pack(fill="both", expand=True, padx=8, pady=8)

        r1 = tk.Frame(card, bg=self.CARD_BG); r1.pack(fill="x", padx=16, pady=(14, 6))
        self._make_label(r1, "Interval (detik):").pack(side="left")
        self.jig_interval_entry = self._make_entry(r1, 30); self.jig_interval_entry.pack(side="right")

        r2 = tk.Frame(card, bg=self.CARD_BG); r2.pack(fill="x", padx=16, pady=6)
        self._make_label(r2, "Jarak (piksel):").pack(side="left")
        self.jig_distance_entry = self._make_entry(r2, 2); self.jig_distance_entry.pack(side="right")

        r3 = tk.Frame(card, bg=self.CARD_BG); r3.pack(fill="x", padx=16, pady=6)
        self._make_label(r3, "Pola gerakan:").pack(side="left")
        self.jig_pattern_var = tk.StringVar(value="linear")
        patterns = ["linear", "circular", "zigzag", "random", "diagonal", "figure8", "wave", "spiral"]
        ttk.Combobox(r3, textvariable=self.jig_pattern_var, values=patterns, state="readonly",
                     width=12, font=("Segoe UI", 10)).pack(side="right")

        tk.Label(card, text=("linear: geser kanan-kiri  |  circular: lingkaran  |  zigzag: kotak\n"
                              "random: acak  |  diagonal: diagonal  |  figure8: angka 8\n"
                              "wave: gelombang  |  spiral: spiral"),
                 font=("Segoe UI", 8), bg=self.CARD_BG, fg=self.TEXT_MUTED, justify="left").pack(padx=16, pady=(8, 8), anchor="w")

        self.jig_start_btn, self.jig_stop_btn = self._make_btn_row(card, self.start_jiggler, self.stop_jiggler)
        tk.Label(card, text="Failsafe: gerakkan mouse ke pojok kiri-atas untuk hentikan darurat.",
                 font=("Segoe UI", 8), bg=self.CARD_BG, fg=self.TEXT_MUTED).pack(pady=(0, 12))

    # -- Clicker tab -- #

    def _build_clicker_tab(self):
        tab = tk.Frame(self.notebook, bg=self.BG)
        self.notebook.add(tab, text=" Auto Clicker ")
        card = self._make_card(tab)
        card.pack(fill="both", expand=True, padx=8, pady=8)

        r1 = tk.Frame(card, bg=self.CARD_BG); r1.pack(fill="x", padx=16, pady=(14, 6))
        self._make_label(r1, "Tombol mouse:").pack(side="left")
        self.click_button_var = tk.StringVar(value="left")
        ttk.Combobox(r1, textvariable=self.click_button_var, values=["left", "right", "middle"],
                     state="readonly", width=10, font=("Segoe UI", 10)).pack(side="right")

        r2 = tk.Frame(card, bg=self.CARD_BG); r2.pack(fill="x", padx=16, pady=6)
        self._make_label(r2, "Interval (detik):").pack(side="left")
        self.click_interval_entry = self._make_entry(r2, 2); self.click_interval_entry.pack(side="right")

        r3 = tk.Frame(card, bg=self.CARD_BG); r3.pack(fill="x", padx=16, pady=6)
        self._make_label(r3, "Jumlah klik (0=tanpa henti):").pack(side="left")
        self.click_count_entry = self._make_entry(r3, 0); self.click_count_entry.pack(side="right")

        r4 = tk.Frame(card, bg=self.CARD_BG); r4.pack(fill="x", padx=16, pady=6)
        self.click_double_var = tk.BooleanVar(value=False)
        tk.Checkbutton(r4, text="Double click", variable=self.click_double_var, bg=self.CARD_BG,
                       fg=self.TEXT, font=("Segoe UI", 10), selectcolor=self.ENTRY_BG,
                       activebackground=self.CARD_BG, activeforeground=self.TEXT).pack(side="left")

        self.click_start_btn, self.click_stop_btn = self._make_btn_row(card, self.start_clicker, self.stop_clicker)

    # -- Actions tab -- #

    def _build_actions_tab(self):
        tab = tk.Frame(self.notebook, bg=self.BG)
        self.notebook.add(tab, text=" Auto Actions ")
        card = self._make_card(tab)
        card.pack(fill="both", expand=True, padx=8, pady=8)

        r1 = tk.Frame(card, bg=self.CARD_BG); r1.pack(fill="x", padx=16, pady=(14, 6))
        self._make_label(r1, "Pilih aksi:").pack(side="left")
        self.action_var = tk.StringVar(value="open_tab")
        self._actions = [
            ("open_tab", "Buka tab baru (Ctrl+T)"), ("close_tab", "Tutup tab (Ctrl+W)"),
            ("scroll_down", "Scroll ke bawah"), ("scroll_up", "Scroll ke atas"),
            ("refresh", "Refresh (Ctrl+R)"), ("switch_app", "Ganti aplikasi (Alt+Tab)"),
            ("type_text", "Ketik teks"), ("volume_mute", "Mute/unmute volume"),
            ("capslock", "Toggle CapsLock"), ("lock_screen", "Lock screen (Win+L)"),
            ("screenshot", "Screenshot"),
        ]
        box = ttk.Combobox(r1, textvariable=self.action_var, values=[v for v, _ in self._actions],
                           state="readonly", width=16, font=("Segoe UI", 10))
        box.pack(side="right")

        r2 = tk.Frame(card, bg=self.CARD_BG); r2.pack(fill="x", padx=16, pady=6)
        self._make_label(r2, "Interval (detik):").pack(side="left")
        self.action_interval_entry = self._make_entry(r2, 10); self.action_interval_entry.pack(side="right")

        r3 = tk.Frame(card, bg=self.CARD_BG); r3.pack(fill="x", padx=16, pady=6)
        self._make_label(r3, "Teks kustom (untuk type_text):").pack(side="left")
        self.action_text_entry = tk.Entry(r3, width=16, font=("Segoe UI", 10), bg=self.ENTRY_BG,
                                          fg=self.TEXT, insertbackground=self.TEXT, relief="flat")
        self.action_text_entry.insert(0, "KeepActive ")
        self.action_text_entry.pack(side="right")

        self._action_map = dict(self._actions)
        self.action_desc = tk.Label(card, text="", font=("Segoe UI", 9), bg=self.CARD_BG,
                                    fg=self.TEXT_MUTED, wraplength=380, justify="left")
        self.action_desc.pack(padx=16, pady=(6, 6), anchor="w")
        box.bind("<<ComboboxSelected>>", self._on_action_change)
        self._on_action_change()

        self.action_start_btn, self.action_stop_btn = self._make_btn_row(card, self.start_action, self.stop_action)

    def _on_action_change(self, event=None):
        self.action_desc.config(text=f"Aksi: {self._action_map.get(self.action_var.get(), '')}")

    # -- Custom Move tab -- #

    def _build_custom_move_tab(self):
        tab = tk.Frame(self.notebook, bg=self.BG)
        self.notebook.add(tab, text=" Custom Move ")
        card = self._make_card(tab)
        card.pack(fill="both", expand=True, padx=8, pady=8)

        r1 = tk.Frame(card, bg=self.CARD_BG); r1.pack(fill="x", padx=16, pady=(14, 6))
        self._make_label(r1, "Koordinat X:").pack(side="left")
        self.move_x_entry = self._make_entry(r1, 500); self.move_x_entry.pack(side="right")

        r2 = tk.Frame(card, bg=self.CARD_BG); r2.pack(fill="x", padx=16, pady=6)
        self._make_label(r2, "Koordinat Y:").pack(side="left")
        self.move_y_entry = self._make_entry(r2, 400); self.move_y_entry.pack(side="right")

        r3 = tk.Frame(card, bg=self.CARD_BG); r3.pack(fill="x", padx=16, pady=6)
        self.move_repeat_var = tk.BooleanVar(value=False)
        tk.Checkbutton(r3, text="Ulangi", variable=self.move_repeat_var, bg=self.CARD_BG,
                       fg=self.TEXT, font=("Segoe UI", 10), selectcolor=self.ENTRY_BG,
                       activebackground=self.CARD_BG, activeforeground=self.TEXT).pack(side="left")

        r4 = tk.Frame(card, bg=self.CARD_BG); r4.pack(fill="x", padx=16, pady=6)
        self._make_label(r4, "Interval ulang (detik):").pack(side="left")
        self.move_interval_entry = self._make_entry(r4, 5); self.move_interval_entry.pack(side="right")

        btn_get = tk.Button(card, text="Ambil posisi mouse saat ini", bg=self.ACCENT, fg="white",
                            font=("Segoe UI", 9), relief="flat", command=self._grab_current_pos)
        btn_get.pack(pady=(8, 4))

        self.move_start_btn, self.move_stop_btn = self._make_btn_row(card, self.start_custom_move, self.stop_custom_move)

    def _grab_current_pos(self):
        x, y = pyautogui.position()
        self.move_x_entry.delete(0, tk.END); self.move_x_entry.insert(0, str(x))
        self.move_y_entry.delete(0, tk.END); self.move_y_entry.insert(0, str(y))

    # -- Keyboard tab -- #

    def _build_keyboard_tab(self):
        tab = tk.Frame(self.notebook, bg=self.BG)
        self.notebook.add(tab, text=" Keyboard ")
        card = self._make_card(tab)
        card.pack(fill="both", expand=True, padx=8, pady=8)

        r1 = tk.Frame(card, bg=self.CARD_BG); r1.pack(fill="x", padx=16, pady=(14, 6))
        self._make_label(r1, "Shortcut (pisahkan dengan +):").pack(side="left")
        self.kb_keys_entry = tk.Entry(r1, width=18, font=("Segoe UI", 10), bg=self.ENTRY_BG,
                                      fg=self.TEXT, insertbackground=self.TEXT, relief="flat")
        self.kb_keys_entry.insert(0, "ctrl+c")
        self.kb_keys_entry.pack(side="right")

        r2 = tk.Frame(card, bg=self.CARD_BG); r2.pack(fill="x", padx=16, pady=6)
        self._make_label(r2, "Interval (detik):").pack(side="left")
        self.kb_interval_entry = self._make_entry(r2, 5); self.kb_interval_entry.pack(side="right")

        tk.Label(card, text="Contoh: ctrl+c, ctrl+v, alt+f4, shift+tab, ctrl+shift+esc, win+d",
                 font=("Segoe UI", 8), bg=self.CARD_BG, fg=self.TEXT_MUTED, justify="left").pack(padx=16, pady=(8, 8), anchor="w")

        self.kb_start_btn, self.kb_stop_btn = self._make_btn_row(card, self.start_keyboard, self.stop_keyboard)

    # -- Activity Log -- #

    def _build_log(self):
        frame = tk.Frame(self.root, bg=self.BG)
        frame.pack(fill="x", padx=16, pady=(4, 12))
        tk.Label(frame, text="Activity Log", font=("Segoe UI", 10, "bold"), bg=self.BG, fg=self.TEXT_MUTED).pack(anchor="w")
        self.log_text = tk.Text(frame, height=6, width=80, font=("Consolas", 9), bg=self.LOG_BG,
                                fg=self.TEXT, relief="flat", state="disabled", wrap="word")
        self.log_text.pack(fill="x", pady=(4, 0))
        btn_frame = tk.Frame(frame, bg=self.BG)
        btn_frame.pack(fill="x", pady=(4, 0))
        tk.Button(btn_frame, text="Clear Log", bg=self.CARD_BG, fg=self.TEXT_MUTED, font=("Segoe UI", 8),
                  relief="flat", command=self._clear_log).pack(side="left")
        self.stop_all_btn = tk.Button(btn_frame, text="HENTIKAN SEMUA", bg=self.DANGER, fg="white",
                                      font=("Segoe UI", 9, "bold"), relief="flat", command=self.stop_all)
        self.stop_all_btn.pack(side="right")

    def _log(self, msg: str):
        timestamp = time.strftime("%H:%M:%S")
        self.root.after(0, lambda: self._append_log(f"[{timestamp}] {msg}"))

    def _append_log(self, line: str):
        self.log_text.config(state="normal")
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    # --- status --- #

    def _set_status(self, active: bool):
        if active:
            self.status_dot.config(fg=self.SUCCESS)
            self.status_text.config(text="Status: AKTIF", fg=self.SUCCESS)
        else:
            self.status_dot.config(fg=self.DANGER)
            self.status_text.config(text="Status: MATI", fg=self.DANGER)

    def _any_active(self) -> bool:
        workers = [self.jiggler_worker, self.clicker_worker, self.action_worker,
                   self.custom_worker, self.keyboard_worker]
        return any(w is not None and w.is_alive() for w in workers)

    def _refresh_status(self):
        self._set_status(self._any_active())

    # --- Start / Stop --- #

    def start_jiggler(self):
        try:
            interval = float(self.jig_interval_entry.get())
            distance = int(self.jig_distance_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Interval angka desimal, jarak bilangan bulat.")
            return
        if interval <= 0 or distance <= 0:
            messagebox.showerror("Error", "Nilai harus > 0.")
            return
        self.jiggler_worker = JigglerWorker(interval, distance, self.jig_pattern_var.get(), self._log)
        self.jiggler_worker.start()
        self.jig_start_btn.config(state="disabled"); self.jig_stop_btn.config(state="normal")
        self._set_status(True)

    def stop_jiggler(self):
        if self.jiggler_worker: self.jiggler_worker.stop()
        self.jig_start_btn.config(state="normal"); self.jig_stop_btn.config(state="disabled")
        self.root.after(500, self._refresh_status)

    def start_clicker(self):
        try:
            interval = float(self.click_interval_entry.get())
            count = int(self.click_count_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Input tidak valid.")
            return
        if interval <= 0 or count < 0:
            messagebox.showerror("Error", "Interval > 0, jumlah >= 0.")
            return
        self.clicker_worker = ClickerWorker(self.click_button_var.get(), interval, count,
                                            self.click_double_var.get(), self._log)
        self.clicker_worker.start()
        self.click_start_btn.config(state="disabled"); self.click_stop_btn.config(state="normal")
        self._set_status(True)

    def stop_clicker(self):
        if self.clicker_worker: self.clicker_worker.stop()
        self.click_start_btn.config(state="normal"); self.click_stop_btn.config(state="disabled")
        self.root.after(500, self._refresh_status)

    def start_action(self):
        try:
            interval = float(self.action_interval_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Interval harus angka.")
            return
        if interval <= 0:
            messagebox.showerror("Error", "Interval > 0.")
            return
        self.action_worker = ActionWorker(self.action_var.get(), interval,
                                          self.action_text_entry.get(), self._log)
        self.action_worker.start()
        self.action_start_btn.config(state="disabled"); self.action_stop_btn.config(state="normal")
        self._set_status(True)

    def stop_action(self):
        if self.action_worker: self.action_worker.stop()
        self.action_start_btn.config(state="normal"); self.action_stop_btn.config(state="disabled")
        self.root.after(500, self._refresh_status)

    def start_custom_move(self):
        try:
            x = int(self.move_x_entry.get())
            y = int(self.move_y_entry.get())
            interval = float(self.move_interval_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Koordinat harus bilangan bulat, interval angka.")
            return
        if interval <= 0:
            messagebox.showerror("Error", "Interval > 0.")
            return
        self.custom_worker = CustomMoveWorker(x, y, self.move_repeat_var.get(), interval, self._log)
        self.custom_worker.start()
        self.move_start_btn.config(state="disabled"); self.move_stop_btn.config(state="normal")
        self._set_status(True)

    def stop_custom_move(self):
        if self.custom_worker: self.custom_worker.stop()
        self.move_start_btn.config(state="normal"); self.move_stop_btn.config(state="disabled")
        self.root.after(500, self._refresh_status)

    def start_keyboard(self):
        keys = self.kb_keys_entry.get().strip()
        if not keys:
            messagebox.showerror("Error", "Masukkan shortcut keyboard.")
            return
        try:
            interval = float(self.kb_interval_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Interval harus angka.")
            return
        if interval <= 0:
            messagebox.showerror("Error", "Interval > 0.")
            return
        self.keyboard_worker = KeyboardShortcutWorker(keys, interval, self._log)
        self.keyboard_worker.start()
        self.kb_start_btn.config(state="disabled"); self.kb_stop_btn.config(state="normal")
        self._set_status(True)

    def stop_keyboard(self):
        if self.keyboard_worker: self.keyboard_worker.stop()
        self.kb_start_btn.config(state="normal"); self.kb_stop_btn.config(state="disabled")
        self.root.after(500, self._refresh_status)

    def stop_all(self):
        self.stop_jiggler(); self.stop_clicker(); self.stop_action()
        self.stop_custom_move(); self.stop_keyboard()
        self._log("Semua otomatisasi dihentikan")
        self._refresh_status()


# ====================================================================== #
#  Entry point
# ====================================================================== #

if __name__ == "__main__":
    root = tk.Tk()
    app = MouseJigglerApp(root)
    root.mainloop()
