import os
import shutil
from urllib.parse import urlparse
import yt_dlp
from pathlib import Path

class AudioDownloader:
    @staticmethod
    def download(url, output_dir, log_callback=None):
        """
        YouTube URLから音声をダウンロードし、ファイルパスを返す。
        """
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"
        }:
            raise ValueError("Enter a valid YouTube URL.")
        if not shutil.which("ffmpeg"):
            raise RuntimeError("FFmpeg is required. Install it and add ffmpeg to PATH.")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # オプション設定
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'outtmpl': os.path.join(output_dir, '%(title)s [%(id)s].%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
            'quiet': True,
            'no_warnings': True,
        }

        # コールバック用のフック
        def progress_hook(d):
            if d['status'] == 'downloading':
                if log_callback:
                    p = d.get('_percent_str', '0%')
                    log_callback(f"Downloading: {p}")
            elif d['status'] == 'finished':
                if log_callback:
                    log_callback("Download received. Converting...")

        ydl_opts['progress_hooks'] = [progress_hook]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if log_callback: log_callback(f"Fetching info for: {url}")
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # 拡張子がmp3に変わるため修正
                final_path = os.path.splitext(filename)[0] + ".mp3"
                if not Path(final_path).is_file() or Path(final_path).stat().st_size == 0:
                    raise RuntimeError("Conversion did not produce an MP3 file.")
                return final_path
        except Exception as e:
            raise e
