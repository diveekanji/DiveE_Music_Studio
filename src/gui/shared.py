import customtkinter as ctk

# === 1. Color Palette (DiveE Theme) ===
COLORS = {
    "bg_dark": "#121212",         # アプリ背景
    "card_bg": "#1E1E1E",         # カード・パネル背景
    "card_border": "#2B2B2B",     # カード枠線
    "card_hover": "#2A2A2A",      # ホバー背景
    
    "accent": "#3B8ED0",          # メインアクション (青)
    "accent_hover": "#36719F",
    
    "success": "#2CC985",         # 実行・完了 (緑)
    "success_hover": "#26A66F",
    
    "danger": "#C0392B",          # 削除・ログアウト (赤)
    "danger_hover": "#E74C3C",
    
    "text_main": "#FFFFFF",       # 本文
    "text_sub": "#AAAAAA",        # サブテキスト
    "input_bg": "#252525",        # 入力欄背景
}

# === 2. Typography ===
FONTS = {
    "h1": ("Roboto Medium", 24),
    "h2": ("Roboto Medium", 20),
    "h3": ("Arial", 14, "bold"),
    "body": ("Arial", 12),
    "small": ("Arial", 11),
    "code": ("Consolas", 12),
}

# === 3. Atomic Components (共通部品) ===

class ModernCard(ctk.CTkFrame):
    """枠線と角丸を持つ共通コンテナ"""
    def __init__(self, parent, title=None, **kwargs):
        # デフォルト値を設定（上書き可能）
        kwargs.setdefault("fg_color", COLORS["card_bg"])
        kwargs.setdefault("border_color", COLORS["card_border"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", 10)
        
        super().__init__(parent, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        
        self.inner_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.inner_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
        self.inner_frame.grid_columnconfigure(0, weight=1)

        if title:
            self.lbl_title = ctk.CTkLabel(self, text=title, font=FONTS["h3"], text_color=COLORS["text_sub"])
            self.lbl_title.grid(row=0, column=0, sticky="w", padx=15, pady=(12, 0))

class PrimaryButton(ctk.CTkButton):
    """メインアクション用ボタン (青/緑)"""
    def __init__(self, parent, text, command, color="accent", **kwargs):
        fg = COLORS[color]
        hover = COLORS[f"{color}_hover"]
        
        # デフォルト値を設定（kwargsに既に含まれている場合は上書きしない）
        kwargs.setdefault("font", ("Roboto Medium", 13))
        kwargs.setdefault("height", 36)
        kwargs.setdefault("corner_radius", 6)
        
        super().__init__(parent, 
                         text=text, 
                         command=command,
                         fg_color=fg, 
                         hover_color=hover,
                         **kwargs)

class SecondaryButton(ctk.CTkButton):
    """サブアクション用ボタン (透明/枠線あり)"""
    def __init__(self, parent, text, command, **kwargs):
        # デフォルト値を設定
        kwargs.setdefault("font", ("Arial", 12))
        kwargs.setdefault("height", 36)
        kwargs.setdefault("corner_radius", 6)
        
        super().__init__(parent, 
                         text=text, 
                         command=command,
                         fg_color="transparent",
                         border_width=1,
                         border_color=COLORS["card_border"],
                         text_color=COLORS["text_sub"],
                         hover_color=COLORS["card_hover"],
                         **kwargs)

class ModernEntry(ctk.CTkEntry):
    """共通スタイルの入力欄"""
    def __init__(self, parent, placeholder="", **kwargs):
        # デフォルト値を設定
        kwargs.setdefault("height", 36)
        kwargs.setdefault("corner_radius", 6)
        
        super().__init__(parent,
                         placeholder_text=placeholder,
                         fg_color=COLORS["input_bg"],
                         border_width=1,
                         border_color=COLORS["card_border"],
                         text_color=COLORS["text_main"],
                         **kwargs)

class StatusBadge(ctk.CTkLabel):
    """ステータス表示用バッジ"""
    def __init__(self, parent, text, status="neutral", **kwargs):
        color_map = {
            "success": COLORS["success"],
            "error": COLORS["danger"],
            "neutral": COLORS["text_sub"]
        }
        
        super().__init__(parent, 
                         text=f"● {text}", 
                         text_color=color_map.get(status, "gray"),
                         font=("Arial", 11, "bold"),
                         **kwargs)

class DummyFile:
    """Noconsole対策"""
    def write(self, x): pass
    def flush(self): pass
    def isatty(self): return False