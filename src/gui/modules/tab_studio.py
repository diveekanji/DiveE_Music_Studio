import threading
import time
import customtkinter as ctk
from tkinter import filedialog
from src.gui.shared import (
    ModernCard, PrimaryButton, SecondaryButton, 
    ModernEntry, SectionHeader, AppColors, AppFonts
)

class TabStudioFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # 2カラムレイアウト (左: 入力ソース, 右: タブプレビュー/エディタ)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        self._init_source_panel()
        self._init_editor_panel()

    def _init_source_panel(self):
        self.left_panel = ModernCard(self)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        
        SectionHeader(self.left_panel, text="Transcription Source").pack(pady=20, padx=20, anchor="w")

        # 1. URL Input (Songsterr / YouTube)
        ctk.CTkLabel(self.left_panel, text="From URL (Songsterr/YouTube)", font=AppFonts.body(), text_color=AppColors.TEXT_SUB).pack(anchor="w", padx=20, pady=(0, 5))
        self.url_entry = ModernEntry(self.left_panel, placeholder_text="Paste URL here...")
        self.url_entry.pack(fill="x", padx=20, pady=(0, 10))
        
        SecondaryButton(self.left_panel, text="Fetch Tab / Audio", command=self._fetch_url).pack(fill="x", padx=20, pady=(0, 20))

        # Divider
        ctk.CTkFrame(self.left_panel, height=2, fg_color=AppColors.BORDER).pack(fill="x", padx=20, pady=10)

        # 2. Local Audio File
        ctk.CTkLabel(self.left_panel, text="From Audio File (AI to MIDI)", font=AppFonts.body(), text_color=AppColors.TEXT_SUB).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.file_btn = SecondaryButton(self.left_panel, text="Select Audio File...", command=self._select_file)
        self.file_btn.pack(fill="x", padx=20, pady=(0, 10))
        
        # Settings for Transcription
        SectionHeader(self.left_panel, text="AI Settings").pack(pady=(20, 10), padx=20, anchor="w")
        
        self.instrument_menu = ctk.CTkOptionMenu(
            self.left_panel,
            values=["Guitar (6-string)", "Bass (4-string)", "Piano"],
            font=AppFonts.body(),
            fg_color=AppColors.BG_ROOT,
            button_color=AppColors.SECONDARY,
            text_color=AppColors.TEXT_MAIN
        )
        self.instrument_menu.pack(fill="x", padx=20, pady=5)

        # Main Action
        self.transcribe_btn = PrimaryButton(
            self.left_panel, 
            text="GENERATE TAB (MIDI)", 
            height=45,
            command=self._start_transcription
        )
        self.transcribe_btn.pack(side="bottom", fill="x", padx=20, pady=20)

    def _init_editor_panel(self):
        self.right_panel = ModernCard(self)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        # Header
        header = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        SectionHeader(header, text="Tab Preview / Editor").pack(side="left")
        
        # Tools (Zoom, Play, etc.)
        tools = ctk.CTkFrame(header, fg_color="transparent")
        tools.pack(side="right")
        SecondaryButton(tools, text="Open in TuxGuitar", width=120, height=30).pack(side="right")

        # Preview Area (Placeholder for Tab Rendering)
        self.preview_area = ctk.CTkTextbox(
            self.right_panel,
            font=("Consolas", 14),
            text_color=AppColors.TEXT_MAIN,
            fg_color="#000000",
            corner_radius=8
        )
        self.preview_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.preview_area.insert("0.0", "Waiting for input...\n\n(Here, the generated ASCII Tab or MIDI visualization will appear.)")

    def _fetch_url(self):
        self.url_entry.configure(state="disabled")
        self.preview_area.delete("0.0", "end")
        self.preview_area.insert("0.0", "Fetching data from URL... (Simulated)")
        self.after(2000, lambda: self.url_entry.configure(state="normal"))

    def _select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav")])
        if file_path:
            self.file_btn.configure(text=file_path.split("/")[-1])

    def _start_transcription(self):
        self.transcribe_btn.configure(state="disabled", text="ANALYZING...")
        
        def _process():
            time.sleep(3) # Simulate heavy AI inference
            self.after(0, self._on_complete)
            
        threading.Thread(target=_process, daemon=True).start()

    def _on_complete(self):
        self.transcribe_btn.configure(state="normal", text="GENERATE TAB (MIDI)")
        self.preview_area.delete("0.0", "end")
        self.preview_area.insert("0.0", "E|------------------------------------|\nB|------------------------------------|\nG|-------7---7-9b11r9-7---------------|\nD|---7h9---9------------9-7-5---------|\nA|------------------------------7-5---|\nE|----------------------------------7-|\n\n(Simulated AI Result)")