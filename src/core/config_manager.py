# src/core/config_manager.py
import json
import os
import sys
from pathlib import Path

def get_app_base_path():
    """実行環境（スクリプト/Exe）に応じたベースパスを取得"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        # main.py のあるディレクトリを基準にする
        return os.path.dirname(os.path.abspath(sys.argv[0]))

class ConfigManager:
    CONFIG_FILE = "config.json"
    
    def __init__(self):
        self.base_path = get_app_base_path()
        self.config_path = os.path.join(self.base_path, self.CONFIG_FILE)
        
        # デフォルト設定（両プロジェクトのマージ）
        self.DEFAULT_CONFIG = {
            # --- Common ---
            "theme": "Dark",
            
            # --- Audio Splitter Settings ---
            "splitter_output_dir": os.path.join(self.base_path, "DiveE_Exports"),
            "model": "htdemucs_6s",

            # --- Tab Studio Settings ---
            "tux_path": r"C:\Program Files\tuxguitar\tuxguitar.exe",
            "tab_output_dir": os.path.join(self.base_path, "Output"),
            "headless_browser": False,
            "keep_gp_file": True,
            "open_folder": True,
            "target_instruments": {
                "bass": True,
                "guitar": False,
                "drum": False,
                "others": False
            }
        }
        self.config = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        """設定ファイルをロード"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except:
                pass
        
        # フォルダ作成の保証
        self._ensure_dirs()

    def _ensure_dirs(self):
        for key in ["splitter_output_dir", "tab_output_dir"]:
            path = self.config.get(key)
            if path:
                try:
                    os.makedirs(path, exist_ok=True)
                except:
                    pass

    def save(self):
        """現在のメモリ上の設定をファイルに書き込む"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Config save error: {e}")

    # ▼▼▼ 追加: SettingsFrameから呼ばれるメソッド ▼▼▼
    def save_config(self, new_config):
        """辞書全体を受け取って更新・保存する"""
        self.config = new_config
        self.save()
    # ▲▲▲ 追加終了 ▲▲▲

    def get(self, key):
        return self.config.get(key, self.DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()