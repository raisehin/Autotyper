import tkinter as tk
from tkinter import ttk, filedialog
import sys
import os
import time
import random
import threading
import pyautogui
import keyboard
import pygetwindow as gw
import ctypes
from datetime import datetime

pyautogui.PAUSE = 0 # Don't change this cause this controls the delay between typing, higher than 0 = choppy ah

# --- Configuration & Constants ---
class AppConfig:
    bg_color = "#1a1a1a"
    card_color = "#141414" 
    accent_color = "#F2C306"
    text_color = "#FFFFFF"
    
    hotkey_start = "F6"
    hotkey_pause = "F7"
    hotkey_stop = "F8"
    hotkey_esc = "ESC"
    
    target_wpm = 60
    humanize_jitter = 0.0
    start_delay = 3
    start_delay_enabled = True
    loop_enabled = False

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- Typing Logic ---
class TypingWorker:
    def __init__(self, text, target_window, log_callback, progress_callback):
        self.text = text
        self.target_window = target_window
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.running = False
        self.paused = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def toggle_pause(self):
        self.paused = not self.paused
        state = "Paused" if self.paused else "Resumed"
        self.log_callback(f"Sequence {state}", "INFO")

    def run(self):
        if AppConfig.start_delay_enabled:
            for i in range(AppConfig.start_delay, 0, -1):
                if not self.running: return
                self.log_callback(f"Sequence starting in {i}s...", "INFO")
                time.sleep(1)
        
        if not self.running: return
        self.log_callback("Typing started", "ACTION")
        
        if self.target_window and self.target_window != "Current Cursor":
            try:
                wins = gw.getWindowsWithTitle(self.target_window)
                if wins:
                    wins[0].activate()
                    time.sleep(0.5)
            except: pass

        while self.running:
            total_chars = len(self.text)
            typed_chars = 0
            
            for char in self.text:
                while self.paused:
                    if not self.running: return
                    time.sleep(0.5)
                
                if not self.running: break
                
                target_delay = 60.0 / (AppConfig.target_wpm * 5)
                if AppConfig.humanize_jitter > 0:
                    delay = max(0.001, target_delay + (target_delay * random.uniform(-AppConfig.humanize_jitter, AppConfig.humanize_jitter)))
                else:
                    delay = target_delay
                
                pyautogui.write(char)
                typed_chars += 1
                time.sleep(delay)
            
            if not AppConfig.loop_enabled or not self.running:
                break
            else:
                self.log_callback("Sequence looping", "INFO")
                time.sleep(0.5)

        if self.running:
            self.log_callback("Typing complete", "SUCCESS")
        self.running = False

# --- UI Components ---
class MGSButton(tk.Button):
    def __init__(self, master, text, desc, command, app, **kwargs):
        super().__init__(master, text=text, command=command, 
                         bg="#1e1e1e", fg="#FFFFFF", activebackground="#f0f0f0", 
                         activeforeground="#0a0a0a", font=("Arial", 11, "bold"),
                         relief="flat", anchor="w", padx=15, pady=5, bd=0, **kwargs)
        self.desc = desc
        self.app = app
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.config(bg="#f0f0f0", fg="#0a0a0a")
        self.app.show_desc(self.desc)

    def on_leave(self, e):
        self.config(bg="#1e1e1e", fg="#FFFFFF")
        self.app.show_desc("")

class AutoTyperTK(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AutoTyper Pro (Tkinter)")
        self.geometry("850x650") 
        self.configure(bg=AppConfig.bg_color)
        self.overrideredirect(True) 
        
        self.worker = None
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.setup_ui()
        self.setup_hotkeys()
        
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)
        
        try:
            myappid = 'hobgoblin.autotyper.lite.v1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except: pass

        icon_path = resource_path("hobgoblin_tech-paper-7098789_1920.png")
        if os.path.exists(icon_path):
            try:
                self.iconphoto(True, tk.PhotoImage(file=icon_path))
            except: pass

    def setup_ui(self):
        self.main_container = tk.Frame(self, bg=AppConfig.bg_color, padx=40, pady=30)
        self.main_container.pack(fill="both", expand=True)

        header = tk.Frame(self.main_container, bg=AppConfig.bg_color)
        header.pack(fill="x", side="top")
        
        tk.Label(header, text="AUTOTYPER", font=("Arial", 24, "bold"), 
                 bg=AppConfig.bg_color, fg="white").pack(side="left")
        
        tk.Button(header, text="✕", command=self.on_closing, bg="#331111", fg="white",
                  font=("Arial", 12, "bold"), relief="flat", bd=0, padx=10, pady=5).pack(side="right")

        # Setup Log Frame first at the bottom
        self.setup_log()

        # Body Frame fills the remaining space between Header and Log
        self.body = tk.Frame(self.main_container, bg=AppConfig.bg_color)
        self.body.pack(fill="both", expand=True, pady=10)
        
        left_panel = tk.Frame(self.body, bg=AppConfig.bg_color, width=300)
        left_panel.pack(side="left", fill="y")
        left_panel.pack_propagate(False)

        self.btn_start = MGSButton(left_panel, "START TYPING", "Begin the automation sequence.", self.start_typing, self)
        self.btn_start.pack(fill="x", pady=1)
        
        self.btn_edit = MGSButton(left_panel, "EDIT TEXT", "Modify the text content to be typed.", lambda: self.show_view(self.view_editor), self)
        self.btn_edit.pack(fill="x", pady=1)
        
        self.btn_target = MGSButton(left_panel, "SELECT WINDOW", "Choose target application window.", lambda: self.show_view(self.view_target), self)
        self.btn_target.pack(fill="x", pady=1)
        
        self.btn_settings = MGSButton(left_panel, "SETTINGS", "Adjust speed, jitter, and delays.", lambda: self.show_view(self.view_settings), self)
        self.btn_settings.pack(fill="x", pady=1)
        
        MGSButton(left_panel, "EXIT", "Close the application.", self.on_closing, self).pack(fill="x", pady=1)

        self.lbl_desc = tk.Label(left_panel, text="", bg="#050505", fg="#cccccc", 
                                 font=("Arial", 10), wraplength=250, justify="left", 
                                 anchor="nw", padx=10, pady=10, height=5)
        self.lbl_desc.pack(fill="x", side="bottom", pady=10)

        self.right_panel = tk.Frame(self.body, bg=AppConfig.card_color, highlightbackground="white", highlightthickness=1)
        self.right_panel.pack(side="right", fill="both", expand=True)

        self.setup_views()

    def setup_views(self):
        self.view_editor = tk.Frame(self.right_panel, bg=AppConfig.card_color)
        tk.Label(self.view_editor, text="TEXT EDITOR", font=("Arial", 12, "bold"), bg=AppConfig.card_color, fg="white").pack(anchor="w", padx=10, pady=10)
        
        self.txt_editor = tk.Text(self.view_editor, bg=AppConfig.bg_color, fg="white", 
                                  insertbackground="white", relief="flat", padx=10, pady=10)
        self.txt_editor.pack(fill="both", expand=True)
        
        editor_btns = tk.Frame(self.view_editor, bg=AppConfig.card_color)
        editor_btns.pack(fill="x", pady=10)
        
        btn_style = {"bg": "#222", "fg": "white", "relief": "flat", "padx": 10}
        tk.Button(editor_btns, text="PASTE", **btn_style, command=self.paste_text).pack(side="left", padx=5)
        tk.Button(editor_btns, text="IMPORT", **btn_style, command=self.import_text).pack(side="left", padx=5)
        tk.Button(editor_btns, text="EXPORT", **btn_style, command=self.export_text).pack(side="left", padx=5)
        tk.Button(editor_btns, text="CLEAR", **btn_style, command=lambda: self.txt_editor.delete("1.0", tk.END)).pack(side="left", padx=5)

        self.view_settings = tk.Frame(self.right_panel, bg=AppConfig.card_color)
        tk.Label(self.view_settings, text="SYSTEM SETTINGS", font=("Arial", 12, "bold"), bg=AppConfig.card_color, fg="white").pack(anchor="w", padx=10, pady=10)
        
        scroll_frame = tk.Frame(self.view_settings, bg=AppConfig.card_color)
        scroll_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(scroll_frame, bg=AppConfig.card_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        setting_content = tk.Frame(canvas, bg=AppConfig.card_color)

        setting_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=setting_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")

        tk.Label(setting_content, text="Target Speed (WPM):", bg=AppConfig.card_color, fg="white").pack(anchor="w")
        self.scale_wpm = tk.Scale(setting_content, from_=10, to=300, orient="horizontal", bg=AppConfig.card_color, fg="white", highlightthickness=0)
        self.scale_wpm.set(AppConfig.target_wpm)
        self.scale_wpm.pack(fill="x")

        tk.Label(setting_content, text="Humanize Jitter:", bg=AppConfig.card_color, fg="white").pack(anchor="w", pady=(10,0))
        self.scale_jitter = tk.Scale(setting_content, from_=0, to=100, orient="horizontal", bg=AppConfig.card_color, fg="white", highlightthickness=0)
        self.scale_jitter.set(int(AppConfig.humanize_jitter * 100))
        self.scale_jitter.pack(fill="x")

        # Start Delay Controls
        delay_frame = tk.Frame(setting_content, bg=AppConfig.card_color)
        delay_frame.pack(fill="x", pady=10)
        
        self.delay_var = tk.BooleanVar(value=AppConfig.start_delay_enabled)
        self.chk_countdown = tk.Checkbutton(delay_frame, text="Enable Start Delay", variable=self.delay_var, 
                                            bg=AppConfig.card_color, fg="white", selectcolor="#1a1a1a", 
                                            activebackground=AppConfig.card_color, command=self.update_config)
        self.chk_countdown.pack(side="left")

        tk.Label(delay_frame, text=" Seconds:", bg=AppConfig.card_color, fg="white").pack(side="left")
        self.delay_spin = tk.Spinbox(delay_frame, from_=1, to=60, width=5, bg="#222", fg="white", bd=0, command=self.update_config)
        self.delay_spin.delete(0, "end")
        self.delay_spin.insert(0, str(AppConfig.start_delay))
        self.delay_spin.pack(side="left", padx=5)

        self.loop_var = tk.BooleanVar(value=AppConfig.loop_enabled)
        tk.Checkbutton(setting_content, text="Loop Mode (Infinite Repeat)", variable=self.loop_var,
                       bg=AppConfig.card_color, fg="white", selectcolor="#1a1a1a", 
                       activebackground=AppConfig.card_color, command=self.update_config).pack(anchor="w", pady=5)

        self.view_target = tk.Frame(self.right_panel, bg=AppConfig.card_color)
        tk.Label(self.view_target, text="TARGET SELECTION", font=("Arial", 12, "bold"), bg=AppConfig.card_color, fg="white").pack(anchor="w", padx=10, pady=10)
        
        self.target_list = ttk.Combobox(self.view_target, state="readonly")
        self.target_list.pack(fill="x", padx=20, pady=10)
        self.refresh_windows()
        
        tk.Button(self.view_target, text="REFRESH WINDOWS", **btn_style, command=self.refresh_windows).pack(padx=20)

        self.current_view = self.view_editor
        self.view_editor.pack(fill="both", expand=True)

    def update_config(self):
        AppConfig.start_delay_enabled = self.delay_var.get()
        try:
            AppConfig.start_delay = int(self.delay_spin.get())
        except: pass
        AppConfig.loop_enabled = self.loop_var.get()

    def setup_log(self):
        self.log_frame = tk.Frame(self.main_container, bg="#0a0a0a", highlightbackground=AppConfig.accent_color, highlightthickness=1)
        self.log_frame.pack(fill="x", side="bottom")
        self.log_frame.pack_propagate(False)
        self.log_frame.config(height=120)
        
        tk.Label(self.log_frame, text="Activity Log", bg="#0a0a0a", fg=AppConfig.accent_color, font=("Arial", 10, "bold")).pack(anchor="w", padx=10)
        
        self.log_text = tk.Text(self.log_frame, bg="#0a0a0a", fg="#DDDDDD", font=("Consolas", 9), borderwidth=0, padx=10)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_config("INFO", foreground="#AAAAAA")
        self.log_text.tag_config("ACTION", foreground="#3498DB")
        self.log_text.tag_config("SUCCESS", foreground="#2ECC71")
        self.log_text.tag_config("ERROR", foreground="#E74C3C")
        self.log_text.tag_config("TIME", foreground="#666666")

        self.log_event("Application initialized (Tkinter)", "INFO")

    def log_event(self, msg, level="INFO"):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{time_str}] ", "TIME")
        self.log_text.insert(tk.END, f"[{level}] ", level)
        self.log_text.insert(tk.END, f"{msg}\n")
        self.log_text.see(tk.END)

    def show_view(self, view):
        self.current_view.pack_forget()
        view.pack(fill="both", expand=True)
        self.current_view = view

    def show_desc(self, text):
        self.lbl_desc.config(text=text)

    def refresh_windows(self):
        windows = ["Current Cursor"]
        try:
            titles = [w.title for w in gw.getAllWindows() if w.title.strip()]
            windows.extend(sorted(titles))
        except: pass
        self.target_list['values'] = windows
        self.target_list.current(0)

    def start_typing(self):
        if self.worker and self.worker.running: return
        text = self.txt_editor.get("1.0", tk.END).strip()
        if not text:
            self.log_event("No text in editor", "ERROR")
            return
        
        self.update_config() 
        AppConfig.target_wpm = self.scale_wpm.get()
        AppConfig.humanize_jitter = self.scale_jitter.get() / 100.0
        
        self.worker = TypingWorker(text, self.target_list.get(), self.log_event, None)
        self.worker.start()

    def setup_hotkeys(self):
        def check_hotkeys():
            while True:
                if keyboard.is_pressed(AppConfig.hotkey_start):
                    self.after(0, self.start_typing)
                if keyboard.is_pressed(AppConfig.hotkey_stop) or keyboard.is_pressed(AppConfig.hotkey_esc):
                    if self.worker: 
                        self.worker.stop()
                        self.after(0, lambda: self.log_event("Emergency Stop", "ERROR"))
                if keyboard.is_pressed(AppConfig.hotkey_pause):
                    if self.worker: self.worker.toggle_pause()
                time.sleep(0.1)
        
        threading.Thread(target=check_hotkeys, daemon=True).start()

    def paste_text(self):
        try:
            self.txt_editor.insert(tk.END, self.clipboard_get())
        except: pass

    def import_text(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.txt_editor.delete("1.0", tk.END)
                self.txt_editor.insert(tk.END, f.read())
            self.log_event(f"Imported from {os.path.basename(path)}", "INFO")

    def export_text(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.txt_editor.get("1.0", tk.END))
            self.log_event(f"Exported to {os.path.basename(path)}", "SUCCESS")

    def start_drag(self, e):
        widget = e.widget
        if any(isinstance(widget, t) for t in [tk.Text, tk.Scale, tk.Button, ttk.Combobox, tk.Spinbox]):
            self.dragging = False
            return
        
        self.dragging = True
        self.x = e.x
        self.y = e.y

    def do_drag(self, e):
        if not hasattr(self, 'dragging') or not self.dragging:
            return
        deltax = e.x - self.x
        deltay = e.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def on_closing(self):
        if self.worker:
            self.worker.stop()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = AutoTyperTK()
    app.mainloop()
