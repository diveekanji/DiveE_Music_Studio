# src/automation/tux_printer.py

import os
import time
import subprocess
import ctypes
import pyautogui
import pyperclip
from pathlib import Path

# Windows API
user32 = ctypes.windll.user32

class TuxGuitarPrinter:
    TUX_PATH = r"C:\Program Files\tuxguitar\tuxguitar.exe"
    
    def __init__(self, tux_path=None):
        # 引数があればそれを使い、なければデフォルト(後方互換用)
        if tux_path:
            self.TUX_PATH = tux_path
        else:
            self.TUX_PATH = r"C:\Program Files\tuxguitar\tuxguitar.exe"

        if not Path(self.TUX_PATH).exists():
            raise FileNotFoundError(f"TuxGuitar not found at: {self.TUX_PATH}\nPlease update the path in Settings.")
        
    def _set_default_printer_to_pdf(self):
        try:
            ps_command = r"(Get-WmiObject -Class Win32_Printer | Where-Object { $_.Name -eq 'Microsoft Print to PDF' }).SetDefaultPrinter()"
            subprocess.run(["powershell", "-Command", ps_command], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("System Printer forced to: Microsoft Print to PDF")
            return True
        except Exception as e:
            print(f"Printer Set Warning: {e}")
            return False

    def _force_focus_window(self, keyword="TuxGuitar"):
        target_hwnd = None
        def enum_callback(hwnd, _):
            nonlocal target_hwnd
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            if keyword.lower() in buff.value.lower() and user32.IsWindowVisible(hwnd):
                target_hwnd = hwnd
                return False 
            return True
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        user32.EnumWindows(EnumWindowsProc(enum_callback), 0)
        if target_hwnd:
            try:
                if user32.IsIconic(target_hwnd):
                    user32.ShowWindow(target_hwnd, 9)
                user32.SetForegroundWindow(target_hwnd)
                time.sleep(0.5)
                return True
            except Exception as e:
                print(f"Focus Error: {e}")
        return False

    def gp_to_pdf(self, gp_file_path, track_index, output_pdf_path):
        gp_path = Path(gp_file_path)
        pdf_path = Path(output_pdf_path)
        
        self._set_default_printer_to_pdf()

        print(f"Launching TuxGuitar with: {gp_path.name}")
        
        # ★修正: 作業ディレクトリ(cwd)をTuxGuitarのインストールフォルダに指定する
        # これを行わないと、依存DLL(fluidsynthなど)の読み込みに失敗してエラーダイアログが出る
        tux_dir = os.path.dirname(self.TUX_PATH)
        proc = subprocess.Popen([self.TUX_PATH, str(gp_path)], cwd=tux_dir)
        
        # スマート待機ロジック (最大20秒)
        print("Waiting for TuxGuitar window...")
        window_found = False
        for _ in range(40): 
            if self._force_focus_window("TuxGuitar"):
                window_found = True
                break
            time.sleep(0.5)
        
        if not window_found:
            print("Warning: Window not found in time, continuing anyway...")
            time.sleep(2)

        # 起動直後の安定化ウェイト
        time.sleep(3.0)

        try:
            self._force_focus_window("TuxGuitar")
            
            # ★トラック切り替えロジックの修正: 印刷オプション画面での操作に戻す
            
            # 1. 印刷オプション画面を開く
            print("Opening Print Options (Ctrl+P)...")
            pyautogui.hotkey('ctrl', 'p')
            time.sleep(1.5) 
            
            # 2. 右矢印キーでトラックを選択
            # (TuxGuitarは起動時 Track 0 なので、そこから相対的に移動)
            if track_index > 0:
                print(f"Selecting Track {track_index} in Dialog (Right Arrow x{track_index})...")
                for _ in range(track_index):
                    pyautogui.press('right')
                    time.sleep(0.1) # 確実に入力させるための短いウェイト
            
            # 3. オプションOK
            print("Pressing OK on Options...")
            pyautogui.press('enter')
            
            # 4. システムダイアログ待ち
            print("Waiting for System Print Dialog...")
            time.sleep(2.0) 
            
            # 5. 印刷ボタンへ移動 (Shift+Tab x3)
            # ※以前お客様側で調整いただいた「3回」を適用
            print("Navigating to Print button...")
            for _ in range(3):
                pyautogui.hotkey('shift', 'tab')
                time.sleep(0.1)
            
            # 6. 実行
            pyautogui.press('enter')
            
            # 7. 保存ダイアログ待ち
            print("Waiting for Save Dialog...")
            time.sleep(3.0)

            # 8. パス入力
            if pdf_path.exists():
                try: os.remove(pdf_path)
                except: pass

            pyperclip.copy(str(pdf_path))
            time.sleep(0.5)
            
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(0.5)
            pyautogui.press('enter') 
            
            print("Waiting for write...")
            time.sleep(5.0)

        finally:
            print("Closing...")
            proc.kill()
            
            if pdf_path.exists():
                print("Success.")
                return True
            else:
                print("Error: PDF not found.")
                return False