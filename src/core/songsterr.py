# src/core/songsterr.py

import os
import time
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

class SongsterrClient:
    AUTH_FILE = "songsterr_auth.json"
    BASE_URL = "https://www.songsterr.com"
    NEW_TAB_URL = "https://www.songsterr.com/new" 

    def __init__(self, headless=True, download_dir=None):
        self.base_dir = Path(os.getcwd())
        self.auth_path = self.base_dir / self.AUTH_FILE
        self.headless = headless
        
        # --- Exe化対応: ブラウザパスの強制設定 ---
        if getattr(sys, 'frozen', False):
            # PyInstallerの一時解凍フォルダパス
            bundle_dir = Path(sys._MEIPASS)
            # 独自に同梱させるフォルダ "playwright-browsers" を指定
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(bundle_dir / "playwright-browsers")
        # ---------------------------------------

        if download_dir:
            self.download_dir = Path(download_dir)
        else:
            self.download_dir = self.base_dir / "temp_downloads"
            
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def login(self):
        """初回ログイン用"""
        print("Launching browser for login...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(locale='ja-JP')
            page = context.new_page()
            page.goto(self.BASE_URL)
            try:
                print("--- ログイン完了後、ブラウザを閉じてください ---")
                page.wait_for_event("close", timeout=0) 
            except Exception:
                pass
            context.storage_state(path=self.auth_path)
            print(f"Login session saved.")
            browser.close()

    def request_transcription_only(self, youtube_url, artist=None, title=None):
        """
        AI採譜のリクエストを行う。
        1文字ずつ入力し、Enterキー送信とJS強制クリックを併用して確実に送信する。
        """
        if not self.auth_path.exists():
            raise FileNotFoundError("認証ファイルがありません。login()してください。")

        print(f"Requesting AI Transcription for: {youtube_url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, args=['--lang=ja-JP'])
            context = browser.new_context(storage_state=self.auth_path, locale='ja-JP')
            page = context.new_page()
            
            page.goto(self.NEW_TAB_URL)
            page.wait_for_load_state("networkidle")
            
            try:
                # 1. YouTube URL入力欄の特定
                input_locator = page.locator("input[type='text']").first
                if page.get_by_placeholder("YouTube").is_visible():
                    input_locator = page.get_by_placeholder("YouTube")
                elif page.get_by_label("YouTube").is_visible():
                    input_locator = page.get_by_label("YouTube")
                
                # フォーカスを当てる
                input_locator.click()
                time.sleep(0.5)

                # ★修正1: 1文字ずつ入力してReactのバリデーションを確実に反応させる
                print("Typing URL sequentially...")
                input_locator.press_sequentially(youtube_url, delay=10)
                time.sleep(1.0) # バリデーション待ち

                # アーティスト・タイトルも同様に入力（もしあれば）
                if artist:
                    try:
                        a_input = page.get_by_placeholder("Artist")
                        if a_input.is_visible():
                            a_input.click()
                            a_input.fill(artist)
                    except: pass
                if title:
                    try:
                        t_input = page.get_by_placeholder("Song")
                        if t_input.is_visible():
                            t_input.click()
                            t_input.fill(title)
                    except: pass
                
                # 入力欄に戻ってEnterを押してみる (これが一番効くことが多い)
                input_locator.click()
                print("Pressing Enter...")
                page.keyboard.press("Enter")
                time.sleep(2.0)

                # ページ遷移チェック (Enterだけで成功した場合)
                if "/new" not in page.url:
                    print("-> Success via Enter key!")
                else:
                    # 2. ボタンを探してJavaScriptで強制クリック
                    print("Enter didn't work. Trying JS click...")
                    
                    # ボタン特定 (aria-labelやtype=submitを優先)
                    target_btn = None
                    
                    # ログにあった aria-label="AIでタブを採譜" をピンポイントで狙う
                    # または汎用的な submit ボタン
                    candidates = [
                        page.locator("button[aria-label='AIでタブを採譜']"),
                        page.locator("button[type='submit']"),
                        page.locator("button:has-text('AI')"),
                        page.locator("button:has-text('採譜')")
                    ]
                    
                    for btn in candidates:
                        if btn.count() > 0 and btn.first.is_visible():
                            target_btn = btn.first
                            break
                    
                    if target_btn:
                        print(f"Target button found: {target_btn.inner_text() or 'Icon Button'}")
                        
                        # ボタンが有効になるまで少し待つ
                        for _ in range(5):
                            if target_btn.is_enabled():
                                break
                            time.sleep(1)
                        
                        # ★修正2: Playwrightのclickではなく、ブラウザ内のJSで直接click()を実行する
                        # これにより「ボタンが無効(disabled)」判定や「重なり」を無視してイベントを発火できる場合がある
                        print("Executing JS click...")
                        target_btn.evaluate("element => element.click()")
                        # 念のためPlaywrightの強制クリックも
                        try:
                            target_btn.click(force=True, timeout=2000)
                        except:
                            pass
                    else:
                        print("Warning: Submit button not found.")

                # 3. ページ遷移待ち
                print("Waiting for page navigation...")
                try:
                    page.wait_for_url(lambda url: "/new" not in url, timeout=30000)
                    print("-> Page navigated successfully. AI job started.")
                except Exception:
                    # エラーメッセージ確認
                    if page.locator("text=Invalid").is_visible():
                        raise RuntimeError("Songsterr rejected the URL.")
                    print("Warning: Navigation timeout. Please check screenshot if job failed.")

            except Exception as e:
                page.screenshot(path="songsterr_req_error.png")
                raise RuntimeError(f"Request failed: {e}")

            browser.close()
            return True

    def download_from_url(self, songsterr_url, artist, title):
        """
        URLを開き、「エクスポート」→「Guitar Pro」の順にクリックしてダウンロードする。
        (page.expect_download を使用した堅牢版)
        """
        print(f"Accessing Songsterr Page: {songsterr_url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, args=['--lang=ja-JP'])
            context = browser.new_context(
                storage_state=self.auth_path,
                accept_downloads=True,
                locale='ja-JP'
            )
            page = context.new_page()
            
            page.goto(songsterr_url)
            page.wait_for_load_state("networkidle")

            try:
                print("Looking for 'Export' (エクスポート) button...")
                export_btn = page.locator("button, a, div[role='button']").filter(has_text=re.compile(r"Export|エクスポート", re.IGNORECASE)).first
                export_btn.wait_for(state="visible", timeout=10000)
                export_btn.click()
                print("Clicked 'Export'.")
                
                time.sleep(1.0)

                print("Looking for 'Guitar Pro' option and waiting for download...")
                with page.expect_download(timeout=30000) as download_info:
                    gp_btn = page.locator("text=Guitar Pro").first
                    gp_btn.wait_for(state="visible", timeout=5000)
                    gp_btn.click()
                    print("Clicked 'Guitar Pro'.")

                download = download_info.value

            except Exception as e:
                print(f"Interaction failed: {e}")
                page.screenshot(path="dl_error.png")
                raise RuntimeError("Download sequence failed. Check dl_error.png")

            safe_filename = re.sub(r'[\\/*?:"<>|]', '_', f"{artist} - {title}.gp")
            saved_path = self.download_dir / safe_filename
            
            if saved_path.exists():
                try: os.remove(saved_path)
                except: pass
            
            download.save_as(saved_path)
            print(f"Downloaded: {saved_path}")
            
            return saved_path