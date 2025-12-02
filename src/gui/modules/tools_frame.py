import os
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk

from src.gui.shared import COLORS, ModernCard, PrimaryButton, SecondaryButton, ModernEntry, StatusBadge
from src.audio.processor import AudioPostProcessor
from src.core.downloader import AudioDownloader

class PracticeToolsFrame(ctk.CTkFrame):
    def __init__(self, parent, config_manager):
        super().__init__(parent, fg_color="transparent")
        self.config = config_manager
        self.target_file_path = None

        # Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === Left Panel (Controls) ===
        self.left_panel = ctk.CTkFrame(self, width=300, corner_radius=10, fg_color=COLORS["card_bg"])
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        self.left_panel.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(self.left_panel, text="PRACTICE TOOLS", font=("Roboto Medium", 20), text_color=COLORS["text_main"]).grid(row=0, column=0, pady=(25, 10))

        # 1. Input Source Card (Splitterと統一)
        self.card_input = ModernCard(self.left_panel, title="Input Source")
        self.card_input.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        
        self.tab_view = ctk.CTkTabview(self.card_input.inner_frame, height=140, 
                                       fg_color="transparent", segmented_button_fg_color=COLORS["input_bg"],
                                       segmented_button_selected_color=COLORS["accent"])
        self.tab_view.pack(fill="x", pady=(0, 10))
        
        self.tab_yt = self.tab_view.add("YouTube")
        self.tab_local = self.tab_view.add("Local File")

        # YouTube Tab
        self.entry_url = ModernEntry(self.tab_yt, placeholder="Paste YouTube URL...")
        self.entry_url.pack(fill="x", pady=15, padx=5)
        
        # Local Tab
        self.btn_browse = SecondaryButton(self.tab_local, text="Choose File", command=self.browse_file)
        self.btn_browse.pack(fill="x", pady=(15, 5), padx=5)
        
        self.lbl_file = ctk.CTkLabel(self.tab_local, text="No file selected", text_color="gray", font=("Arial", 11))
        self.lbl_file.pack()

        # 2. Options Card
        self.card_opts = ModernCard(self.left_panel, title="Transform Options")
        self.card_opts.grid(row=2, column=0, padx=15, pady=10, sticky="ew")
        
        # Inner Grid
        self.opts_inner = ctk.CTkFrame(self.card_opts.inner_frame, fg_color="transparent")
        self.opts_inner.pack(fill="x", pady=5)
        self.opts_inner.grid_columnconfigure(1, weight=1)

        # Speed
        ctk.CTkLabel(self.opts_inner, text="Speed:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.slider_speed = ctk.CTkSlider(self.opts_inner, from_=0.5, to=1.5, command=self.on_speed_slider)
        self.slider_speed.set(1.0)
        self.slider_speed.grid(row=0, column=1, sticky="ew", padx=5)
        self.entry_speed = ModernEntry(self.opts_inner, width=50)
        self.entry_speed.grid(row=0, column=2, padx=5)
        self.entry_speed.insert(0, "1.00")
        self.entry_speed.bind("<Return>", self.on_speed_entry)
        self.entry_speed.bind("<FocusOut>", self.on_speed_entry)

        # Pitch
        ctk.CTkLabel(self.opts_inner, text="Pitch:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.slider_pitch = ctk.CTkSlider(self.opts_inner, from_=-12, to=12, number_of_steps=24, command=self.on_pitch_slider)
        self.slider_pitch.set(0)
        self.slider_pitch.grid(row=1, column=1, sticky="ew", padx=5)
        self.entry_pitch = ModernEntry(self.opts_inner, width=50)
        self.entry_pitch.grid(row=1, column=2, padx=5)
        self.entry_pitch.insert(0, "0")
        self.entry_pitch.bind("<Return>", self.on_pitch_entry)
        self.entry_pitch.bind("<FocusOut>", self.on_pitch_entry)

        # Checkboxes
        self.var_click = ctk.BooleanVar(value=True)
        self.chk_click = ctk.CTkCheckBox(self.card_opts.inner_frame, text="Add Metronome (4-beat)", variable=self.var_click, font=("Arial", 12))
        self.chk_click.pack(anchor="w", padx=10, pady=5)
        
        self.var_chord = ctk.BooleanVar(value=False)
        self.chk_chord = ctk.CTkCheckBox(self.card_opts.inner_frame, text="Analyze Chords", variable=self.var_chord, font=("Arial", 12))
        self.chk_chord.pack(anchor="w", padx=10, pady=5)

        # Main Action
        self.btn_run = PrimaryButton(self.left_panel, text="PROCESS & SAVE", command=self.start_processing, color="success")
        self.btn_run.grid(row=3, column=0, padx=15, pady=20, sticky="ew")


        # === Right Panel (Result & Log) ===
        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        # Analysis Result Card
        self.card_result = ModernCard(self.right_panel, title="ANALYSIS RESULT")
        self.card_result.grid(row=0, column=0, sticky="nsew")
        self.card_result.inner_frame.grid_rowconfigure(0, weight=1)
        self.card_result.inner_frame.grid_columnconfigure(0, weight=1)

        self.txt_result = ctk.CTkTextbox(self.card_result.inner_frame, font=("Consolas", 12), fg_color=COLORS["bg_dark"])
        self.txt_result.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.txt_result.insert("0.0", "Chord analysis will appear here...")
        self.txt_result.configure(state="disabled")
        
        # Open Folder Btn
        self.btn_open_folder = SecondaryButton(self.card_result.inner_frame, text="Open Output Folder", command=self.open_output_folder)
        self.btn_open_folder.grid(row=1, column=0, sticky="e", pady=10)

        # Status Bar
        self.status_bar = ctk.CTkFrame(self.right_panel, height=30, fg_color="transparent")
        self.status_bar.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        
        self.lbl_status = StatusBadge(self.status_bar, text="Ready", status="neutral")
        self.lbl_status.pack(side="left")

    # --- Sync Logic ---
    def on_speed_slider(self, val):
        self.entry_speed.delete(0, "end")
        self.entry_speed.insert(0, f"{float(val):.2f}")

    def on_speed_entry(self, event=None):
        try:
            val = float(self.entry_speed.get())
            if 0.1 <= val <= 3.0: self.slider_speed.set(val)
        except ValueError: pass

    def on_pitch_slider(self, val):
        self.entry_pitch.delete(0, "end")
        self.entry_pitch.insert(0, f"{int(val)}")

    def on_pitch_entry(self, event=None):
        try:
            val = float(self.entry_pitch.get())
            self.slider_pitch.set(val)
        except ValueError: pass

    # --- Core Logic ---
    def log(self, message):
        self.lbl_status.configure(text=f" {message}", text_color=COLORS["text_sub"])

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.m4a *.flac")])
        if path:
            self.target_file_path = path
            self.lbl_file.configure(text=os.path.basename(path), text_color=COLORS["text_main"])
            self.btn_run.configure(state="normal")

    def open_output_folder(self):
        path = self.config.get("splitter_output_dir")
        if os.path.exists(path):
            os.startfile(path)

    def start_processing(self):
        # 入力チェック
        mode = self.tab_view.get() # "YouTube" or "Local File"
        target = None
        
        if mode == "YouTube":
            url = self.entry_url.get().strip()
            if not url:
                messagebox.showwarning("Error", "Please enter a YouTube URL.")
                return
            target = url
        else:
            if not self.target_file_path:
                messagebox.showwarning("Error", "Please select a file.")
                return
            target = self.target_file_path

        self.btn_run.configure(state="disabled", text="Processing...")
        self.txt_result.configure(state="normal")
        self.txt_result.delete("0.0", "end")
        self.txt_result.configure(state="disabled")
        
        try: speed = float(self.entry_speed.get())
        except: speed = self.slider_speed.get()
        try: pitch = float(self.entry_pitch.get())
        except: pitch = self.slider_pitch.get()
            
        add_click = self.var_click.get()
        analyze_chord = self.var_chord.get()
        output_dir = self.config.get("splitter_output_dir") 
        
        threading.Thread(target=self.run_thread, 
                         args=(mode, target, output_dir, speed, pitch, add_click, analyze_chord), 
                         daemon=True).start()

    def run_thread(self, mode, target, output_dir, speed, pitch, click, chord):
        try:
            def update_status(msg):
                self.log(msg)
            
            process_path = ""
            
            # 1. Download if YouTube
            if mode == "YouTube":
                update_status("Downloading from YouTube...")
                try:
                    process_path = AudioDownloader.download(target, output_dir, log_callback=update_status)
                except Exception as e:
                    raise RuntimeError(f"Download failed: {e}")
            else:
                process_path = target

            # 2. Process
            update_status("Processing Audio...")
            output_path, chord_list = AudioPostProcessor.process_file(
                process_path, output_dir, 
                add_click=click, speed=speed, pitch_semitones=pitch, 
                analyze_chord=chord, progress_callback=update_status
            )
            
            if chord_list:
                self.after(0, lambda: self._show_chords(chord_list))
            else:
                self.after(0, lambda: self._show_chords(["No chords detected."]))
            
            update_status(f"Done")
            self.after(0, lambda: messagebox.showinfo("Success", f"Saved to:\n{os.path.basename(output_path)}"))
            
        except Exception as e:
            update_status(f"Error: {str(e)}")
            print(e)
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, lambda: self.btn_run.configure(state="normal", text="PROCESS & SAVE"))

    def _show_chords(self, lines):
        self.txt_result.configure(state="normal")
        self.txt_result.insert("0.0", "\n".join(lines))
        self.txt_result.configure(state="disabled")