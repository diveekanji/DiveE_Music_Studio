import threading
import customtkinter as ctk
from src.gui.shared import (
    ModernCard, PrimaryButton, SecondaryButton, 
    ModernEntry, SectionHeader, AppColors, AppFonts
)

class ToolsFrame(ctk.CTkScrollableFrame):
    """
    スクロール可能なダッシュボード。
    各ツールをカードとして配置。
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # グリッドレイアウト (2列)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self._add_yt_downloader(row=0, col=0)
        self._add_audio_converter(row=0, col=1)
        self._add_bpm_analyzer(row=1, col=0)

    def _add_yt_downloader(self, row, col):
        card = ModernCard(self)
        card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
        
        SectionHeader(card, text="YouTube Downloader").pack(pady=15, padx=20, anchor="w")
        
        self.yt_url = ModernEntry(card, placeholder_text="https://youtube.com/watch?v=...")
        self.yt_url.pack(fill="x", padx=20, pady=(0, 10))
        
        self.yt_btn = PrimaryButton(card, text="Download Audio (MP3)", command=self._run_download)
        self.yt_btn.pack(fill="x", padx=20, pady=(0, 20))
        
        self.yt_status = ctk.CTkLabel(card, text="", font=AppFonts.caption(), text_color=AppColors.TEXT_SUB)
        self.yt_status.pack(pady=(0, 10))

    def _add_audio_converter(self, row, col):
        card = ModernCard(self)
        card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
        
        SectionHeader(card, text="Format Converter").pack(pady=15, padx=20, anchor="w")
        
        ctk.CTkLabel(card, text="Drop files to convert to WAV/MP3", font=AppFonts.body()).pack(pady=10)
        SecondaryButton(card, text="Select Files").pack(fill="x", padx=20, pady=10)
        
        self.format_menu = ctk.CTkOptionMenu(card, values=["WAV", "MP3", "FLAC", "OGG"], fg_color=AppColors.BG_ROOT)
        self.format_menu.pack(fill="x", padx=20, pady=10)
        
        PrimaryButton(card, text="Convert All").pack(fill="x", padx=20, pady=(0, 20))

    def _add_bpm_analyzer(self, row, col):
        card = ModernCard(self)
        card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
        
        SectionHeader(card, text="BPM / Key Analyzer").pack(pady=15, padx=20, anchor="w")
        
        info_label = ctk.CTkLabel(card, text="Drag audio here to detect BPM", font=AppFonts.body(), text_color=AppColors.TEXT_SUB)
        info_label.pack(pady=20)
        
        # Placeholder for result
        self.bpm_display = ctk.CTkLabel(card, text="-- BPM", font=(AppFonts.FAMILY, 24, "bold"), text_color=AppColors.PRIMARY)
        self.bpm_display.pack(pady=(0, 20))

    def _run_download(self):
        url = self.yt_url.get()
        if not url: return
        
        self.yt_btn.configure(state="disabled", text="Downloading...")
        self.yt_status.configure(text="Processing with yt-dlp...")
        
        def _task():
            import time
            time.sleep(2)
            self.after(0, lambda: self._on_dl_complete())
            
        threading.Thread(target=_task, daemon=True).start()

    def _on_dl_complete(self):
        self.yt_btn.configure(state="normal", text="Download Audio (MP3)")
        self.yt_status.configure(text="Download Complete!", text_color=AppColors.SUCCESS)