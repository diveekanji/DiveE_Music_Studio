import os
import traceback
import shutil
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
from pathlib import Path

# Core Modules
from src.core.youtube import YouTubeUploader
from src.core.songsterr import SongsterrClient
from src.core.gmail import GmailClient
from src.core.gp_manager import GPManager
from src.automation.tux_printer import TuxGuitarPrinter

# New: Local Transcriber
from src.audio.transcriber import AudioTranscriber

# Shared UI
from src.gui.shared import COLORS, ModernCard, PrimaryButton, SecondaryButton, ModernEntry, StatusBadge

class TabStudioFrame(ctk.CTkFrame):
    def __init__(self, parent, config_manager):
        super().__init__(parent, fg_color="transparent")
        self.config = config_manager
        
        # Data
        self.audio_path = None
        self.gp_path = None
        self.renamed_gp_path = None
        self.track_data = []
        
        self.update_paths()

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === Left Panel (Controls) ===
        self.left_panel = ctk.CTkFrame(self, width=300, corner_radius=10, fg_color=COLORS["card_bg"])
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        self.left_panel.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(self.left_panel, text="TAB STUDIO", font=("Roboto Medium", 20), text_color=COLORS["text_main"]).grid(row=0, column=0, pady=(25, 10))

        # 1. Input Source Card
        self.card_input = ModernCard(self.left_panel, title="1. Input Source")
        self.card_input.grid(row=1, column=0, padx=15, pady=10, sticky="ew")

        self.btn_select_file = SecondaryButton(self.card_input.inner_frame, text="Select Audio File", command=self.select_audio)
        self.btn_select_file.pack(fill="x", pady=5)
        
        self.lbl_file_name = ctk.CTkLabel(self.card_input.inner_frame, text="No file selected", font=("Arial", 11), text_color="gray")
        self.lbl_file_name.pack(pady=(0, 10))

        self.btn_select_gp = SecondaryButton(self.card_input.inner_frame, text="Select GP File (Skip AI)", command=self.select_gp)
        self.btn_select_gp.pack(fill="x", pady=5)

        # 2. Online Generation (Songsterr)
        self.card_online = ModernCard(self.left_panel, title="2. Online Gen (Songsterr)")
        self.card_online.grid(row=2, column=0, padx=15, pady=10, sticky="ew")

        self.entry_artist = ModernEntry(self.card_online.inner_frame, placeholder="Artist Name")
        self.entry_artist.pack(fill="x", pady=5)
        self.entry_title = ModernEntry(self.card_online.inner_frame, placeholder="Song Title")
        self.entry_title.pack(fill="x", pady=5)
        self.entry_manual_url = ModernEntry(self.card_online.inner_frame, placeholder="YouTube / Songsterr URL")
        self.entry_manual_url.pack(fill="x", pady=5)

        self.btn_start = PrimaryButton(self.left_panel, text="GENERATE TABS (ONLINE)", command=self.start_process, color="success")
        self.btn_start.grid(row=3, column=0, padx=15, pady=(10, 20), sticky="ew")

        # 3. Local Generation (Beta) - NEW!
        self.card_local = ModernCard(self.left_panel, title="3. Local Gen (Beta)")
        self.card_local.grid(row=4, column=0, padx=15, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.card_local.inner_frame, text="Converts Audio to MIDI directly.\nBest for Bass lines.", 
                     font=("Arial", 11), text_color="gray").pack(pady=(0, 5))

        self.btn_local_gen = SecondaryButton(self.card_local.inner_frame, text="Audio to MIDI (Local)", command=self.start_local_gen)
        self.btn_local_gen.pack(fill="x", pady=5)


        # === Right Panel (Tracks & Log) ===
        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid_rowconfigure(0, weight=1) # Tracks takes space
        self.right_panel.grid_columnconfigure(0, weight=1)

        # Tracks Card
        self.tracks_card = ModernCard(self.right_panel, title="DETECTED TRACKS")
        self.tracks_card.grid(row=0, column=0, sticky="nsew")
        self.tracks_card.inner_frame.grid_rowconfigure(0, weight=1)
        self.tracks_card.inner_frame.grid_columnconfigure(0, weight=1)

        self.track_frame = ctk.CTkScrollableFrame(self.tracks_card.inner_frame, fg_color="transparent", label_text="")
        self.track_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.track_checkboxes = []

        self.btn_print = PrimaryButton(self.tracks_card.inner_frame, text="Export Selected to PDF", command=self.start_printing, color="accent")
        self.btn_print.grid(row=1, column=0, sticky="ew", padx=15, pady=15)
        self.btn_print.configure(state="disabled")

        # Log Card (Bottom)
        self.log_card = ModernCard(self.right_panel, title="PROCESS LOG")
        self.log_card.grid(row=1, column=0, sticky="ew", pady=(15, 0))
        
        self.log_textbox = ctk.CTkTextbox(self.log_card.inner_frame, height=120, font=("Consolas", 11), 
                                          fg_color=COLORS["bg_dark"], text_color=COLORS["text_sub"])
        self.log_textbox.pack(fill="both", padx=10, pady=5)
        self.log_textbox.configure(state="disabled")

        self.log("Tab Studio Module Loaded.")
        self.log(f"Output: {self.OUTPUT_DIR}")


    # --- Logic ---

    def update_paths(self):
        self.OUTPUT_DIR = Path(self.config.get("tab_output_dir"))
        self.DOWNLOAD_DIR = self.OUTPUT_DIR.parent / "temp_downloads"
        try:
            self.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
            self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        except: pass

    def log(self, message, clear=False):
        def _write():
            self.log_textbox.configure(state="normal")
            if clear:
                self.log_textbox.delete("0.0", "end")
            self.log_textbox.insert("end", f"> {message}\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        self.after(0, _write)

    def select_audio(self):
        initial_dir = str(self.OUTPUT_DIR.parent) if self.OUTPUT_DIR.parent.exists() else "/"
        file_path = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Audio Files", "*.mp3 *.wav *.m4a")])
        if file_path:
            self.audio_path = file_path
            self.gp_path = None
            self.lbl_file_name.configure(text=os.path.basename(file_path), text_color="white")
            self.entry_manual_url.delete(0, "end")
            self.log(f"File Selected: {os.path.basename(file_path)}")

    def select_gp(self):
        initial_dir = str(self.DOWNLOAD_DIR) if self.DOWNLOAD_DIR.exists() else "/"
        file_path = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Guitar Pro Files", "*.gp")])
        if file_path:
            self.gp_path = Path(file_path)
            self.audio_path = None
            self.lbl_file_name.configure(text=os.path.basename(file_path), text_color="#AAA")
            self.log(f"Debug GP Mode: {os.path.basename(file_path)}")

    # --- Online Process ---
    def start_process(self):
        artist = self.entry_artist.get()
        title = self.entry_title.get()
        manual_url = self.entry_manual_url.get().strip()

        if not artist or not title:
             messagebox.showwarning("Info", "Artist and Title are required for Songsterr.")
             return

        mode = "normal"
        if self.gp_path:
            mode = "debug_gp"
        elif "songsterr.com" in manual_url:
            mode = "direct_songsterr"
        elif not manual_url and not self.audio_path:
            messagebox.showwarning("Info", "Select Audio, GP file, or enter URL.")
            return

        self.btn_start.configure(state="disabled", text="Processing...")
        self.log("Starting ONLINE process...", clear=True)
        
        threading.Thread(target=self.run_automation_flow, args=(artist, title, manual_url, mode), daemon=True).start()

    def run_automation_flow(self, artist, title, manual_url, mode):
        try:
            is_headless = self.config.get("headless_browser")

            if mode == "debug_gp":
                self.log(f"Mode: GP Debug\nTarget: {self.gp_path.name}")
                if not self.gp_path.exists():
                    raise FileNotFoundError("GP file not found.")
            
            elif mode == "direct_songsterr":
                self.log(f"Mode: Direct Songsterr Download\nURL: {manual_url}")
                songsterr = SongsterrClient(headless=is_headless, download_dir=self.DOWNLOAD_DIR)
                if not songsterr.auth_path.exists():
                    self.log("Login required...")
                    songsterr.login()
                self.gp_path = songsterr.download_from_url(manual_url, artist, title)
                self.log(f"Downloaded.")

            else:
                yt_url = manual_url
                if not yt_url:
                    self.log("Phase 1: YouTube Uploading...")
                    try:
                        uploader = YouTubeUploader()
                        yt_url = uploader.upload(self.audio_path, f"{artist} - {title}")
                        self.log(f"Upload OK: {yt_url}")
                    except Exception as e:
                        if "uploadLimitExceeded" in str(e):
                            self.log("[Error] Upload limit reached. Use manual URL.")
                            self.after(0, lambda: self.btn_start.configure(state="normal", text="GENERATE TABS (ONLINE)"))
                            return
                        else:
                            raise e
                else:
                    self.log(f"Phase 1: Skipped (YouTube URL provided).")

                self.log("Phase 2: Requesting AI Transcription...")
                songsterr = SongsterrClient(headless=is_headless, download_dir=self.DOWNLOAD_DIR)
                if not songsterr.auth_path.exists():
                    self.log("Login required...")
                    songsterr.login()
                
                songsterr.request_transcription_only(yt_url, artist=artist, title=title)
                self.log("Request sent.")

                self.log("Phase 3: Waiting for Email...")
                gmail = GmailClient()
                target_url = gmail.wait_for_completion_email(f"{artist} - {title}")
                self.log(f"Email received.")

                self.log("Phase 4: Downloading GP...")
                self.gp_path = songsterr.download_from_url(target_url, artist, title)
                self.log(f"Downloaded.")

            self.log("Phase 5: Analyzing Tracks...")
            gp_manager = GPManager(self.gp_path)
            self.renamed_gp_path = str(self.gp_path).replace(".gp", "_renamed.gp")
            self.track_data = gp_manager.analyze_and_rename_tracks(output_path=self.renamed_gp_path)
            
            self.after(0, self.update_track_ui)

        except Exception as e:
            self.log(f"Error: {e}")
            traceback.print_exc()
            self.after(0, lambda: self.btn_start.configure(state="normal", text="GENERATE TABS (ONLINE)"))

    # --- Local Generation Logic ---
    def start_local_gen(self):
        if not self.audio_path:
            messagebox.showwarning("Info", "Please select an Audio File first.")
            return
        
        self.btn_local_gen.configure(state="disabled", text="Processing...")
        self.log("Starting LOCAL generation...", clear=True)
        
        threading.Thread(target=self.run_local_gen_flow, args=(self.audio_path,), daemon=True).start()

    def run_local_gen_flow(self, audio_path):
        try:
            self.log("Mode: Local AI (Basic Pitch)")
            
            # MIDI生成
            midi_path = AudioTranscriber.audio_to_midi(
                audio_path, 
                str(self.OUTPUT_DIR), 
                log_callback=self.log
            )
            
            self.log(f"MIDI Generated: {os.path.basename(midi_path)}")
            self.log("Opening in TuxGuitar (Manual Import needed)...")
            
            # TuxGuitarを開く
            tux_path = self.config.get("tux_path")
            if os.path.exists(tux_path):
                # MIDIファイルをTuxGuitarで開く (インポートダイアログが出るはず)
                os.system(f'"{tux_path}" "{midi_path}"')
                self.log("TuxGuitar launched.")
            else:
                self.log("TuxGuitar not found. Please open the MIDI file manually.")
            
            self.after(0, lambda: messagebox.showinfo("Done", f"MIDI file created:\n{midi_path}"))
            
        except Exception as e:
            self.log(f"Local Gen Error: {e}")
            traceback.print_exc()
        finally:
            self.after(0, lambda: self.btn_local_gen.configure(state="normal", text="Audio to MIDI (Local)"))

    # --- Shared UI Logic ---
    def update_track_ui(self):
        for widget in self.track_frame.winfo_children():
            widget.destroy()
        self.track_checkboxes = []
        
        targets = self.config.get("target_instruments")
        
        for track in self.track_data:
            should_check = False
            t_name = track['new_name'].lower()
            
            if track['is_bass'] and targets.get("bass"): should_check = True
            elif "guitar" in t_name and targets.get("guitar"): should_check = True
            elif "drum" in t_name and targets.get("drum"): should_check = True
            elif targets.get("others") and not (track['is_bass'] or "guitar" in t_name or "drum" in t_name): should_check = True

            var = ctk.BooleanVar(value=should_check)
            chk = ctk.CTkCheckBox(self.track_frame, text=f"[{track['index']}] {track['new_name']}", variable=var, font=("Arial", 12))
            chk.grid(row=track['index'], column=0, padx=10, pady=5, sticky="w")
            
            self.track_checkboxes.append({"index": track['index'], "var": var, "name": track['new_name']})

        self.btn_print.configure(state="normal")
        self.btn_start.configure(state="normal", text="GENERATE TABS (ONLINE)")

    def start_printing(self):
        self.btn_print.configure(state="disabled")
        selected_tracks = [t for t in self.track_checkboxes if t['var'].get()]
        
        if not selected_tracks:
            messagebox.showwarning("Info", "Please select at least one track.")
            self.btn_print.configure(state="normal")
            return

        artist = self.entry_artist.get() or "Unknown"
        title = self.entry_title.get() or "Song"
        threading.Thread(target=self.run_printing_flow, args=(selected_tracks, artist, title), daemon=True).start()

    def run_printing_flow(self, selected_tracks, artist, title):
        try:
            tux_path = self.config.get("tux_path")
            printer = TuxGuitarPrinter(tux_path=tux_path)
            
            self.log(f"Phase 6: PDF Exporting...")
            
            for item in selected_tracks:
                track_idx = item['index']
                track_name = item['name']
                safe_track_name = track_name.replace("/", "_")
                pdf_filename = f"{artist} - {title} ({safe_track_name}).pdf"
                output_path = self.OUTPUT_DIR / pdf_filename
                
                self.log(f"Printing: {track_name} ...")
                success = printer.gp_to_pdf(self.renamed_gp_path, track_idx, str(output_path))
                
                if success:
                    self.log(f"-> OK: {pdf_filename}")
                else:
                    self.log(f"-> Failed: {track_name}")

            if self.config.get("keep_gp_file"):
                gp_filename = f"{artist} - {title}.gp"
                gp_dest = self.OUTPUT_DIR / gp_filename
                try:
                    shutil.copy2(self.renamed_gp_path, gp_dest)
                except Exception as e:
                    self.log(f"GP Save Error: {e}")

            self.log("ALL DONE!")
            messagebox.showinfo("Success", "All PDFs generated successfully!")

            if self.config.get("open_folder"):
                os.startfile(self.OUTPUT_DIR)

        except Exception as e:
            self.log(f"Print Error: {e}")
        finally:
            self.after(0, lambda: self.btn_print.configure(state="normal"))