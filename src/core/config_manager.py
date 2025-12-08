import sys
from pathlib import Path

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._init_paths()
        return cls._instance

    def _init_paths(self):
        """パスの初期化（PyInstallerと開発環境の両方に対応）"""
        if getattr(sys, 'frozen', False):
            # PyInstallerでビルドされた場合
            self.base_path = Path(sys._MEIPASS)
            self.app_data_path = Path.home() / "Documents" / "DiveE_Data"
        else:
            # 開発環境
            self.base_path = Path(__file__).parent.parent.parent
            self.app_data_path = self.base_path / "data"

        # アセットパス
        self.assets_path = self.base_path / "assets"
        self.fonts_path = self.assets_path / "fonts"
        self.models_path = self.app_data_path / "models"

        # 必要なディレクトリの作成
        self.app_data_path.mkdir(parents=True, exist_ok=True)
        self.models_path.mkdir(parents=True, exist_ok=True)

    def get_font_path(self, font_name: str) -> str:
        """フォントファイルのパスを取得"""
        font_file = self.fonts_path / font_name
        if font_file.exists():
            return str(font_file)
        return ""  # 見つからない場合は空文字を返す（CTKがデフォルトを使用）

# シングルトンインスタンス
config = ConfigManager()