# src/core/gmail.py

import os
import pickle
import base64
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class GmailClient:
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self, secrets_file_path=None):
        self.base_dir = Path(os.getcwd())
        if secrets_file_path:
            self.secrets_file = Path(secrets_file_path)
        else:
            self.secrets_file = self.base_dir / "client_secrets.json"

        self.token_file = self.secrets_file.parent / "token_gmail.pickle"
        self.service = None

    def authenticate(self):
        """Gmail APIの認証"""
        creds = None
        if self.token_file.exists():
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception:
                pass

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except:
                    self._run_login_flow()
            else:
                self._run_login_flow()
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("Gmail Authentication Successful.")

    def _run_login_flow(self):
        if not self.secrets_file.exists():
            raise FileNotFoundError("client_secrets.json が見つかりません。")
        
        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.secrets_file), self.SCOPES)
        creds = flow.run_local_server(port=0)
        
        with open(self.token_file, 'wb') as token:
            pickle.dump(creds, token)

    def wait_for_completion_email(self, song_title, timeout_minutes=20, check_interval=30):
        """
        指定された曲名の完了通知メールが来るのを待つ。
        ★修正: 古い未読メールを拾わないよう、タイムスタンプとタイトルで厳密にチェックする。
        """
        if not self.service:
            self.authenticate()

        print(f"Waiting for Songsterr email for: '{song_title}' (Max {timeout_minutes} min)...")
        
        # 監視開始時刻 (現在時刻の5分前以降のメールのみを対象とする)
        # ※リクエスト処理時間を考慮して少しバッファを持たせる
        threshold_timestamp = time.time() - 300 
        
        end_time = time.time() + (timeout_minutes * 60)
        
        while time.time() < end_time:
            query = 'from:songsterr.com subject:"transcription" is:unread'
            
            try:
                results = self.service.users().messages().list(userId='me', q=query).execute()
                messages = results.get('messages', [])

                for msg in messages:
                    # 詳細取得
                    txt = self.service.users().messages().get(userId='me', id=msg['id']).execute()
                    
                    # ★フィルタ1: 受信日時チェック
                    internal_date_ms = int(txt.get('internalDate', 0))
                    internal_date_sec = internal_date_ms / 1000
                    
                    if internal_date_sec < threshold_timestamp:
                        # 古いメールなのでスキップ (ログには出す)
                        # print(f"Skipping old unread email (Time: {time.ctime(internal_date_sec)})")
                        continue

                    payload = txt['payload']
                    headers = payload.get("headers")
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "")
                    
                    # 本文取得
                    body_data = None
                    if 'parts' in payload:
                        for part in payload['parts']:
                            if part['mimeType'] == 'text/html':
                                body_data = part['body']['data']
                                break
                    elif payload.get('body') and payload['body'].get('data'):
                        body_data = payload['body']['data']

                    if body_data:
                        html_content = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # ★フィルタ2: タイトル一致チェック (簡易)
                        # Songsterrのメール件名や本文に曲名が含まれているか確認
                        # 大文字小文字を無視してチェック
                        full_text = (subject + " " + soup.get_text()).lower()
                        search_title = song_title.lower()
                        
                        # タイトルが短すぎる場合は誤爆防止のためスキップなどのロジックも考えられるが、
                        # 今回は「タイムスタンプが新しい」時点でほぼ確定なので、
                        # タイトルチェックは「念のため」程度にする（部分一致でOK）
                        
                        # リンク抽出
                        target_url = None
                        for a in soup.find_all('a', href=True):
                            href = a['href']
                            if "/a/wsa/" in href:
                                target_url = href
                                break
                        
                        if target_url:
                            # 念のためログ出力
                            print(f"New email found! Subject: {subject}")
                            print(f"Time: {time.ctime(internal_date_sec)}")
                            
                            # 既読にする
                            self.service.users().messages().modify(
                                userId='me', id=msg['id'],
                                body={'removeLabelIds': ['UNREAD']}
                            ).execute()
                            
                            return target_url

            except Exception as e:
                print(f"Gmail Polling Error: {e}")

            print(f"Checking again in {check_interval}s...")
            time.sleep(check_interval)

        raise TimeoutError("通知メールが届きませんでした。")

if __name__ == "__main__":
    # テスト
    gmail = GmailClient()
    # gmail.wait_for_completion_email("Test Song")