import os
import threading
import demucs.separate
from tkinter import filedialog, messagebox
import customtkinter as ctk
import yt_dlp
from pydub import AudioSegment

from src.gui.shared import COLORS, ModernCard, PrimaryButton, SecondaryButton, ModernEntry, DummyFile, StatusBadge
from src.core.downloader import AudioDownloader

class StemSplitterFrame(ctk.CTkFrame):
    def __init__(self, parent, config_manager):
        super().__init__(parent, fg_color="transparent")
        self.config = config_manager

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.target_file_path = None  
        self.result_stem_dir = None   
        self.stems_vars = {}          

        # === Left Panel (Controls) ===
        self.left_panel = ctk.CTkFrame(self, width=300, corner_radius=10, fg_color=COLORS["card_bg"])
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        self.left_panel.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(self.left_panel, text="AI SPLITTER", font=("Roboto Medium", 20), text_color=COLORS["text_main"]).grid(row=0, column=0, pady=(25, 10))

        # 1. Input Source Card
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
        self.btn_browse = SecondaryButton(self.tab_local, text="Choose File", command=self.select_local_file)
        self.btn_browse.pack(fill="x", pady=(15, 5), padx=5)
        
        self.lbl_local_filename = ctk.CTkLabel(self.tab_local, text="No file selected", text_color="gray", font=("Arial", 11))
        self.lbl_local_filename.pack()

        # 2. Actions
        self.btn_start = PrimaryButton(self.left_panel, text="START SEPARATION", command=self.start_process, color="success")
        self.btn_start.grid(row=2, column=0, padx=15, pady=20, sticky="ew")
        
        # === Right Panel (Mixer) ===
        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        # Mixer Card
        self.mixer_card = ModernCard(self.right_panel, title="MIXER & STEMS")
        self.mixer_card.grid(row=0, column=0, sticky="nsew")
        self.mixer_card.inner_frame.grid_rowconfigure(0, weight=1) 
        self.mixer_card.inner_frame.grid_columnconfigure(0, weight=1)

        self.mixer_scroll = ctk.CTkScrollableFrame(self.mixer_card.inner_frame, fg_color="transparent", label_text="")
        self.mixer_scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.mixer_placeholder = ctk.CTkLabel(self.mixer_scroll, text="Process audio to see stems here.", text_color="gray", font=("Arial", 14))
        self.mixer_placeholder.pack(pady=80)

        # Mixer Controls
        self.mixer_controls = ctk.CTkFrame(self.mixer_card.inner_frame, fg_color="transparent")
        self.mixer_controls.grid(row=1, column=0, sticky="ew", pady=10)
        
        self.btn_export_mix = PrimaryButton(self.mixer_controls, text="Export Mix (mp3)", command=self.start_mix_export, color="accent")
        self.btn_export_mix.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.btn_export_mix.configure(state="disabled")
        
        # ▼▼▼ 修正: widthをコンストラクタ引数に移動 ▼▼▼
        self.btn_open_folder = SecondaryButton(self.mixer_controls, text="Open Folder", command=self.open_output_folder, width=100)
        self.btn_open_folder.pack(side="right")
        # ▲▲▲ 修正終了 ▲▲▲

        # Status Bar
        self.status_bar = ctk.CTkFrame(self.right_panel, height=30, fg_color="transparent")
        self.status_bar.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        
        self.lbl_status = StatusBadge(self.status_bar, text="Ready", status="neutral")
        self.lbl_status.pack(side="left")

        self.log(f"Splitter Ready. Output: {self.config.get('splitter_output_dir')}")

    # --- Logic ---
    def log(self, message):
        self.lbl_status.configure(text=f" {message}", text_color=COLORS["text_sub"])
        print(f"[Splitter] {message}") 

    def select_local_file(self):
        path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.m4a *.flac")])
        if path:
            self.target_file_path = path
            self.lbl_local_filename.configure(text=os.path.basename(path), text_color=COLORS["text_main"])
            self.log(f"Selected: {os.path.basename(path)}")

    def open_output_folder(self):
        path = self.config.get("splitter_output_dir")
        if os.path.exists(path): os.startfile(path)

    def start_process(self):
        current_tab = self.tab_view.get()
        mode = "youtube" if current_tab == "YouTube" else "local"
        target = self.entry_url.get().strip() if mode == "youtube" else self.target_file_path

        if mode == "youtube" and not target:
            messagebox.showwarning("Error", "Enter YouTube URL.")
            return
        if mode == "local" and not target:
            messagebox.showwarning("Error", "Select a file.")
            return

        self.btn_start.configure(state="disabled", text="Processing...")
        self.log("Starting process...")
        
        threading.Thread(target=self.run_separation_flow, args=(mode, target), daemon=True).start()

    def run_separation_flow(self, mode, target):
        try:
            output_dir = self.config.get("splitter_output_dir")
            model = self.config.get("model")
            if not os.path.exists(output_dir): os.makedirs(output_dir)

            audio_path = ""

            # 1. Download / Prepare
            if mode == "youtube":
                self.log(f"Downloading from YouTube...")
                try:
                    # 共通ダウンローダーを使用
                    audio_path = AudioDownloader.download(target, output_dir, log_callback=self.log)
                except Exception as e:
                    raise RuntimeError(f"Download failed: {e}")
            else:
                self.log(f"Processing local file...")
                audio_path = target

            # 2. Separate
            self.log(f"Separating Stems with AI ({model})...")
            import sys
            # Noconsole対策
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            sys.stdout = DummyFile()
            sys.stderr = DummyFile()

            try:
                args = ["-n", model, "--out", output_dir, audio_path]
                demucs.separate.main(args)
            except Exception as e:
                sys.stdout = original_stdout
                sys.stderr = original_stderr
                raise e
            finally:
                sys.stdout = original_stdout
                sys.stderr = original_stderr

            song_name = os.path.splitext(os.path.basename(audio_path))[0]
            self.result_stem_dir = os.path.join(output_dir, model, song_name)
            
            self.log("Separation Complete.")
            self.after(0, self.setup_mixer_ui)

        except Exception as e:
            self.log(f"Error: {e}")
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, lambda: self.btn_start.configure(state="normal", text="START SEPARATION"))
            
    def setup_mixer_ui(self):
        for widget in self.mixer_scroll.winfo_children(): widget.destroy()
        self.stems_vars = {}
        if not self.result_stem_dir or not os.path.exists(self.result_stem_dir): return

        stems = [f for f in os.listdir(self.result_stem_dir) if f.endswith(".wav")]
        for stem in stems:
            stem_name = os.path.splitext(stem)[0]
            color = COLORS["text_main"]
            if "guitar" in stem_name: color = "#E67E22"
            elif "piano" in stem_name: color = "#9B59B6"
            elif "bass" in stem_name: color = "#3498DB"
            elif "drum" in stem_name: color = "#E74C3C"
            elif "vocal" in stem_name: color = "#F1C40F"
            
            var = ctk.BooleanVar(value=True)
            row_f = ctk.CTkFrame(self.mixer_scroll, fg_color="transparent")
            row_f.pack(fill="x", pady=5)
            
            chk = ctk.CTkCheckBox(row_f, text=stem_name.upper(), variable=var, text_color=color, 
                                  font=("Arial", 14, "bold"), fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], width=24, height=24)
            chk.pack(side="left", padx=10)
            self.stems_vars[stem_name] = var

        self.btn_export_mix.configure(state="normal")
        self.btn_open_folder.configure(state="normal")
        self.log("Stems loaded.")

    def start_mix_export(self):
        if not self.result_stem_dir: return
        self.btn_export_mix.configure(state="disabled", text="Mixing...")
        threading.Thread(target=self.run_mixing_flow, daemon=True).start()

    def run_mixing_flow(self):
        try:
            self.log("Generating Mix...")
            from pydub import AudioSegment
            combined = None
            active_stems = []
            for stem_name, var in self.stems_vars.items():
                if var.get():
                    wav_path = os.path.join(self.result_stem_dir, stem_name + ".wav")
                    audio = AudioSegment.from_wav(wav_path)
                    if combined is None: combined = audio
                    else: combined = combined.overlay(audio)
                    active_stems.append(stem_name)
            
            if combined is None: return

            song_name = os.path.basename(self.result_stem_dir)
            suffix = "_CustomMix"
            all_keys = list(self.stems_vars.keys())
            if len(active_stems) == len(all_keys): suffix = "_FullMix"
            elif len(all_keys) - len(active_stems) == 1:
                missing = [s for s in all_keys if s not in active_stems][0]
                suffix = f"_No{missing.capitalize()}"

            save_path = os.path.join(self.config.get("splitter_output_dir"), f"{song_name}{suffix}.mp3")
            combined.export(save_path, format="mp3")
            self.log(f"Exported: {os.path.basename(save_path)}")
            self.after(0, lambda: messagebox.showinfo("Success", "Mix Exported!"))
        except Exception as e:
            self.log(f"Mix Error: {e}")
        finally:
            self.after(0, lambda: self.btn_export_mix.configure(state="normal", text="Export Mix (mp3)"))