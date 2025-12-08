import customtkinter as ctk
from typing import Optional, Tuple, Union, Callable
from src.core.config_manager import config

# --- 1. Design Tokens (定数定義) ---

class AppColors:
    """モダンDAW風カラーパレット"""
    # 背景色
    BG_ROOT = "#121212"       # アプリ全体の背景
    BG_CARD = "#1E1E1E"       # カード/パネル背景
    BG_HOVER = "#2C2C2C"      # ホバー時の背景

    # アクセントカラー
    PRIMARY = "#3B8ED0"       # CustomTkinter標準ブルー
    PRIMARY_HOVER = "#36719F"
    SECONDARY = "#4A4A4A"     # サブボタン等
    
    # 機能色
    SUCCESS = "#00C853"       # 成功・完了
    WARNING = "#FFAB00"       # 注意
    ERROR = "#D50000"         # エラー
    
    # テキスト
    TEXT_MAIN = "#FFFFFF"     # メインテキスト
    TEXT_SUB = "#B0B0B0"      # サブテキスト・ラベル
    BORDER = "#333333"        # 境界線

class AppFonts:
    """フォント設定"""
    FONT_FILE = "NotoSansJP-Medium.ttf" 
    FAMILY = "Roboto Medium" 

    @classmethod
    def load_custom_font(cls):
        font_path = config.get_font_path(cls.FONT_FILE)
        if font_path:
            ctk.FontManager.load_font(font_path)

    @classmethod
    def header(cls): return (cls.FAMILY, 24, "bold")
    @classmethod
    def title(cls): return (cls.FAMILY, 18, "bold")
    @classmethod
    def body(cls): return (cls.FAMILY, 14)
    @classmethod
    def caption(cls): return (cls.FAMILY, 12)
    @classmethod
    def code(cls): return ("Consolas", 13)


# --- 2. Custom Components (UI部品) ---

class ModernCard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        # デフォルト値を設定しつつ、外部指定(kwargs)があればそれを優先
        fg_color = kwargs.pop("fg_color", AppColors.BG_CARD)
        border_color = kwargs.pop("border_color", AppColors.BORDER)
        
        super().__init__(
            master, 
            fg_color=fg_color,
            corner_radius=12,
            border_width=1,
            border_color=border_color,
            **kwargs
        )

class PrimaryButton(ctk.CTkButton):
    def __init__(self, master, text: str, command: Callable = None, **kwargs):
        # kwargsから取り出し（指定がなければデフォルト値を使用）
        height = kwargs.pop("height", 36)
        fg_color = kwargs.pop("fg_color", AppColors.PRIMARY)
        hover_color = kwargs.pop("hover_color", AppColors.PRIMARY_HOVER)
        text_color = kwargs.pop("text_color", AppColors.TEXT_MAIN)
        
        super().__init__(
            master,
            text=text,
            command=command,
            font=AppFonts.body(),
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            corner_radius=8,
            height=height,
            **kwargs
        )

class SecondaryButton(ctk.CTkButton):
    def __init__(self, master, text: str, command: Callable = None, **kwargs):
        height = kwargs.pop("height", 36)
        fg_color = kwargs.pop("fg_color", "transparent")
        border_color = kwargs.pop("border_color", AppColors.SECONDARY)
        text_color = kwargs.pop("text_color", AppColors.TEXT_SUB)
        hover_color = kwargs.pop("hover_color", AppColors.BG_HOVER)

        super().__init__(
            master,
            text=text,
            command=command,
            font=AppFonts.body(),
            fg_color=fg_color,
            border_width=1,
            border_color=border_color,
            hover_color=hover_color,
            text_color=text_color,
            corner_radius=8,
            height=height,
            **kwargs
        )

class ModernEntry(ctk.CTkEntry):
    def __init__(self, master, placeholder_text: str = "", **kwargs):
        height = kwargs.pop("height", 36)
        fg_color = kwargs.pop("fg_color", AppColors.BG_ROOT)
        text_color = kwargs.pop("text_color", AppColors.TEXT_MAIN)
        placeholder_text_color = kwargs.pop("placeholder_text_color", AppColors.TEXT_SUB)
        border_color = kwargs.pop("border_color", AppColors.BORDER)

        super().__init__(
            master,
            placeholder_text=placeholder_text,
            font=AppFonts.body(),
            fg_color=fg_color,
            border_color=border_color,
            text_color=text_color,
            placeholder_text_color=placeholder_text_color,
            corner_radius=8,
            height=height,
            **kwargs
        )

class StatusBadge(ctk.CTkLabel):
    def __init__(self, master, status: str = "IDLE", mode: str = "info", **kwargs):
        color_map = {
            "success": AppColors.SUCCESS,
            "warning": AppColors.WARNING,
            "error": AppColors.ERROR,
            "info": AppColors.SECONDARY
        }
        bg_color = color_map.get(mode, AppColors.SECONDARY)

        super().__init__(
            master,
            text=f" {status} ",
            font=AppFonts.caption(),
            fg_color=bg_color,
            text_color="#FFFFFF",
            corner_radius=6,
            **kwargs
        )
    
    def update_status(self, status: str, mode: str = "info"):
        color_map = {
            "success": AppColors.SUCCESS,
            "warning": AppColors.WARNING,
            "error": AppColors.ERROR,
            "info": AppColors.SECONDARY
        }
        self.configure(text=f" {status} ", fg_color=color_map.get(mode, AppColors.SECONDARY))

class SectionHeader(ctk.CTkLabel):
    def __init__(self, master, text: str, **kwargs):
        text_color = kwargs.pop("text_color", AppColors.TEXT_MAIN)
        super().__init__(
            master,
            text=text,
            font=AppFonts.title(),
            text_color=text_color,
            anchor="w",
            **kwargs
        )