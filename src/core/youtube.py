# src/core/youtube.py

import os
import subprocess
import pickle
import json
import tempfile
import time
from pathlib import Path
from PIL import Image

# Google API
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubeUploader:
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']
    
    def __init__(self, secrets_file_path=None):
        """
        secrets_file_path: ユーザーが用意した client_secrets.json のパス。
        指定がない場合はカレントディレクトリを探す。
        """
        self.base_dir = Path(os.getcwd())
        
        if secrets_file_path:
            self.secrets_file = Path(secrets_file_path)
        else:
            self.secrets_file = self.base_dir / "client_secrets.json"

        # トークンファイル設定
        self.token_file = self.secrets_file.parent / f"token_{self.secrets_file.stem}.pickle"
        self.youtube = None

    def is_setup_complete(self):
        return self.secrets_file.exists()

    def authenticate(self):
        """Googleアカウントで認証を行う"""
        if not self.is_setup_complete():
             raise FileNotFoundError(
                 f"認証ファイルが見つかりません: {self.secrets_file}\n"
                 "Google Cloud Platformで 'OAuth 2.0 Client ID' (JSON) を取得し、"
                 "アプリに読み込ませてください。"
             )

        creds = None
        if self.token_file.exists():
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception:
                print("Token corrupted, re-authenticating...")

        # トークンがない、または無効な場合の処理
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    # リフレッシュ試行
                    creds.refresh(Request())
                    # ★修正: リフレッシュ成功時もここで build する必要があるため、後続の共通処理に流す
                except Exception:
                    # リフレッシュ失敗時は再ログインフローへ
                    self._run_login_flow()
                    return # _run_login_flow内でself.youtubeがセットされるのでここで終了
            else:
                # リフレッシュトークンがない場合は再ログインフローへ
                self._run_login_flow()
                return # _run_login_flow内でself.youtubeがセットされるのでここで終了

        # ★修正: キャッシュ有効 or リフレッシュ成功時の共通処理
        # ここで確実に self.youtube を生成する
        self.youtube = build('youtube', 'v3', credentials=creds)
        print("YouTube Authentication Successful.")

    def _run_login_flow(self):
        """ブラウザ認証フローを実行"""
        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.secrets_file), self.SCOPES)
        creds = flow.run_local_server(port=0)
        
        with open(self.token_file, 'wb') as token:
            pickle.dump(creds, token)
        
        self.youtube = build('youtube', 'v3', credentials=creds)
        print("YouTube Authentication Successful (New Login).")

    def _create_background_image(self, output_path):
        """黒背景画像を生成"""
        img = Image.new('RGB', (1280, 720), color='black')
        img.save(output_path)

    def _convert_audio_to_video(self, audio_path):
        """
        FFmpegを使って音声ファイルを動画(mp4)に変換する。
        ★重要: iCloud同期との競合を防ぐため、OSのTempフォルダに作成する。
        """
        audio_path = Path(audio_path)
        
        # システムの一時フォルダを取得 (例: C:\Users\User\AppData\Local\Temp\...)
        temp_dir = Path(tempfile.gettempdir()) / "BassTabStudio_Temp"
        temp_dir.mkdir(exist_ok=True)
        
        output_video_path = temp_dir / f"{audio_path.stem}_converted.mp4"
        image_path = temp_dir / "temp_bg.jpg"
        
        self._create_background_image(image_path)
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-i", str(audio_path),
            "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p", "-shortest",
            str(output_video_path)
        ]
        
        try:
            # ログ抑制
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg conversion failed: {e.stderr.decode('utf-8', errors='ignore')}")
        except FileNotFoundError:
             raise FileNotFoundError("FFmpegが見つかりません。FFmpegをインストールしてください。")
        finally:
            if image_path.exists():
                try:
                    os.remove(image_path)
                except:
                    pass
                
        return output_video_path

    def upload(self, audio_file_path, title, description="Uploaded by BassTabStudio"):
        """YouTubeへアップロードし、URLを返す"""
        if not self.youtube:
            self.authenticate()

        video_path = self._convert_audio_to_video(audio_file_path)
        media = None # 変数初期化
        
        try:
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': ['BassTabStudio'],
                    'categoryId': '10'
                },
                'status': {
                    'privacyStatus': 'unlisted',
                    'selfDeclaredMadeForKids': False
                }
            }

            print(f"Uploading to YouTube: {title} ...")
            
            # ここでファイルが開かれる
            media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
            
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Uploaded {int(status.progress() * 100)}%")

            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"Upload Complete! URL: {video_url}")
            return video_url

        finally:
            # ★重要: MediaFileUploadオブジェクトを破棄してファイルロックを解除
            if media:
                del media
            
            # 少し待機してから削除（Windowsのファイルシステム用）
            if video_path.exists():
                try:
                    time.sleep(0.5) 
                    os.remove(video_path)
                except PermissionError:
                    print(f"Warning: Temp file could not be deleted (Locked): {video_path}")
                    # ロックされていてもTempフォルダなので、次回のOS再起動時やクリーナー等で消えるため放置でOK

if __name__ == "__main__":
    # テスト設定
    test_secrets = r"client_secrets.json"
    # iCloud Driveのパスでも、Temp経由で変換されるため問題なくなります
    test_audio = r"C:\Users\haruk\iCloudDrive\Automation\姫君バンケット.wav"
    
    if os.path.exists(test_secrets) and os.path.exists(test_audio):
        uploader = YouTubeUploader(test_secrets)
        try:
            url = uploader.upload(test_audio, "Test Upload via BassTabStudio")
            print(f"URL: {url}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Test failed: secrets file or audio file not found.")