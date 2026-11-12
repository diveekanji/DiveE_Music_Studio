import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
from src.gui.modules.splitter import SplitterFrame
from src.gui.modules.tab_studio import TabStudioFrame
from src.gui.modules.tools import ToolsFrame
from src.gui.modules.settings import SettingsFrame
from src.gui.shared import AppColors, AppFonts

# DnD対応のため、ctk.CTk と TkinterDnD.DnDWrapper を多重継承
class DiveEMusicStudioApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self) # DnD機能の初期化

        # --- Window Setup ---
        self.title("DiveE MUSIC STUDIO")
        self.geometry("1200x800")
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        AppFonts.load_custom_font()

        # グリッド構成
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Main Layout ---
        self.main_container = ctk.CTkTabview(
            self, 
            fg_color=AppColors.BG_ROOT, 
            text_color=AppColors.TEXT_SUB,
            segmented_button_fg_color=AppColors.BG_CARD,
            segmented_button_selected_color=AppColors.PRIMARY,
            segmented_button_selected_hover_color=AppColors.PRIMARY_HOVER,
            corner_radius=12
        )
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # タブ作成
        self.tab_splitter = self.main_container.add("AI Splitter")
        self.tab_studio = self.main_container.add("Tab Studio")
        self.tab_tools = self.main_container.add("Tools")
        self.tab_settings = self.main_container.add("Settings")

        # フォント適用
        for button in self.main_container._segmented_button._buttons_dict.values():
            button.configure(font=AppFonts.body())

        # --- Module Loading ---
        # Splitter画面 (selfを渡すことでDnDイベントをバインド可能にする)
        self.splitter_frame = SplitterFrame(self.tab_splitter, app_root=self)
        self.splitter_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab Studio画面
        self.studio_frame = TabStudioFrame(self.tab_studio)
        self.studio_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tools画面
        self.tools_frame = ToolsFrame(self.tab_tools)
        self.tools_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Settings画面
        self.settings_frame = SettingsFrame(self.tab_settings)
        self.settings_frame.pack(fill="both", expand=True, padx=10, pady=10)

if __name__ == "__main__":
    app = DiveEMusicStudioApp()
    app.mainloop()