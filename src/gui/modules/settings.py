import customtkinter as ctk
import os
from src.gui.shared import (
    ModernCard, PrimaryButton, SecondaryButton, 
    ModernEntry, SectionHeader, AppColors, AppFonts
)
from src.core.config_manager import config

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # センター寄せレイアウト
        self.container = ModernCard(self)
        self.container.pack(fill="both", expand=True, padx=40, pady=40)
        
        SectionHeader(self.container, text="Application Settings").pack(pady=20, padx=30, anchor="w")

        # Paths
        self._create_setting_row("Bundled Models", str(config.base_path / "vendor" / "models"))
        self._create_setting_row("Bundled FFmpeg", str(config.base_path / "vendor" / "ffmpeg" / "bin"))
        self._create_setting_row("Output Path", str(config.app_data_path / "outputs"))
        
        # Appearance
        SectionHeader(self.container, text="Appearance").pack(pady=(30, 10), padx=30, anchor="w")
        
        self.theme_menu = ctk.CTkOptionMenu(
            self.container,
            values=["Dark (Default)", "Light"],
            command=self._change_theme,
            fg_color=AppColors.BG_ROOT,
            text_color=AppColors.TEXT_MAIN
        )
        self.theme_menu.pack(anchor="w", padx=30, pady=5)
        
        # System Actions
        SectionHeader(self.container, text="System").pack(pady=(30, 10), padx=30, anchor="w")
        
        btn_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=10)
        
        SecondaryButton(btn_frame, text="Open Data Folder", command=self._open_data_folder).pack(side="left", padx=(0, 10))
        SecondaryButton(btn_frame, text="Clear Cache (Not implemented)", state="disabled", command=None, fg_color=AppColors.ERROR, border_color=AppColors.ERROR, text_color="white").pack(side="left")

        # Version Info
        ctk.CTkLabel(self.container, text="DiveE MUSIC STUDIO v1.0.0", font=AppFonts.caption(), text_color=AppColors.TEXT_SUB).pack(side="bottom", pady=20)

    def _create_setting_row(self, label, value):
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        frame.pack(fill="x", padx=30, pady=5)
        
        ctk.CTkLabel(frame, text=label, width=120, anchor="w", font=AppFonts.body()).pack(side="left")
        entry = ModernEntry(frame)
        entry.insert(0, value)
        entry.configure(state="readonly")
        entry.pack(side="left", fill="x", expand=True, padx=(10, 0))

    def _change_theme(self, mode):
        ctk.set_appearance_mode(mode)

    def _open_data_folder(self):
        os.startfile(config.app_data_path)
