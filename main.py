# main.py
import sys
import os
import multiprocessing
import customtkinter as ctk
from pathlib import Path

# srcフォルダをパスに追加
sys.path.append(str(Path(__file__).parent))

from src.core.config_manager import ConfigManager
from src.gui.shared import COLORS

# 各機能フレーム
from src.gui.modules.splitter_frame import StemSplitterFrame
from src.gui.modules.tab_studio_frame import TabStudioFrame
from src.gui.modules.tools_frame import PracticeToolsFrame
from src.gui.modules.settings_frame import SettingsFrame

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class DiveEMusicStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 設定ロード
        self.config_manager = ConfigManager()
        ctk.set_appearance_mode(self.config_manager.get("theme"))

        # ウィンドウ設定
        self.title("DiveE MUSIC STUDIO")
        self.geometry("1280x800")
        self.configure(fg_color=COLORS["bg_dark"])
        
        # グリッド構成
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === 1. サイドバー ===
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLORS["card_bg"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # ロゴ
        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, pady=(30, 30), padx=20, sticky="ew")
        ctk.CTkLabel(self.logo_frame, text="DiveE", font=("Roboto Medium", 28), text_color=COLORS["accent"]).pack(side="left")
        ctk.CTkLabel(self.logo_frame, text=" STUDIO", font=("Roboto Medium", 28), text_color="white").pack(side="left")

        # ナビゲーションボタン
        self.btn_splitter = self._create_nav_btn("Stem Splitter", self.show_splitter, 1, "AI Audio Separation")
        self.btn_tab = self._create_nav_btn("Tab Studio", self.show_tab_studio, 2, "Auto Score Gen")
        self.btn_tools = self._create_nav_btn("Practice Tools", self.show_tools, 3, "BPM & Stretch")
        
        # スペーサー後の設定ボタン
        self.btn_settings = self._create_nav_btn("Settings", self.show_settings, 9, "Config & Accounts")

        # フッター
        ctk.CTkLabel(self.sidebar, text="v1.0.0", text_color="gray", font=("Arial", 10)).grid(row=11, column=0, pady=20)

        # === 2. コンテンツエリア ===
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

        # フレーム初期化
        self.frames = {}
        self.frames["splitter"] = StemSplitterFrame(self.content_area, self.config_manager)
        self.frames["tab"] = TabStudioFrame(self.content_area, self.config_manager)
        self.frames["tools"] = PracticeToolsFrame(self.content_area, self.config_manager)
        self.frames["settings"] = SettingsFrame(self.content_area, self.config_manager)

        # 初期表示
        self.show_splitter()

    def _create_nav_btn(self, text, command, row, subtitle=None):
        # ボタンを内包するフレーム（サブタイトル表示用）
        frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frame.grid(row=row, column=0, padx=10, pady=8, sticky="ew")
        
        btn = ctk.CTkButton(
            frame, 
            text=text, 
            command=command,
            height=40,
            font=("Arial", 14, "bold"),
            fg_color="transparent", 
            text_color="#DDD",
            anchor="w",
            hover_color=COLORS["card_hover"],
            corner_radius=8
        )
        btn.pack(fill="x")
        
        if subtitle:
            ctk.CTkLabel(frame, text=subtitle, font=("Arial", 11), text_color="gray", anchor="w").pack(fill="x", padx=10)
            
        return btn

    def _reset_nav(self):
        for btn in [self.btn_splitter, self.btn_tab, self.btn_tools, self.btn_settings]:
            btn.configure(fg_color="transparent", text_color="#DDD")
        
        for frame in self.frames.values():
            frame.grid_forget()

    def _activate(self, btn, frame_key):
        self._reset_nav()
        btn.configure(fg_color=COLORS["accent"], text_color="white")
        self.frames[frame_key].grid(row=0, column=0, sticky="nsew")

    def show_splitter(self): self._activate(self.btn_splitter, "splitter")
    def show_tab_studio(self): self._activate(self.btn_tab, "tab")
    def show_tools(self): self._activate(self.btn_tools, "tools")
    def show_settings(self): self._activate(self.btn_settings, "settings")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = DiveEMusicStudio()
    app.mainloop()