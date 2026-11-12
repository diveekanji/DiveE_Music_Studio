import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import soundfile as sf
import numpy as np
from src.audio.separator import separate_audio, STEMS
from src.core.downloader import AudioDownloader


class SeparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "日本語 input.wav"
        sf.write(self.source, np.zeros((4410, 2)), 44100)
        self.output = self.root / "outputs"

    def produce(self, command, **kwargs):
        self.assertEqual(command[1:3], ["-m", "demucs.separate"])
        self.assertEqual(command[-1], str(self.source.resolve()))
        self.assertEqual(command[command.index("--device") + 1], "cpu")
        folder = Path(command[command.index("--out") + 1]) / "htdemucs" / self.source.stem
        folder.mkdir(parents=True)
        for stem in STEMS:
            sf.write(folder / f"{stem}.wav", np.zeros((4410, 2)), 44100)
        return subprocess.CompletedProcess(command, 0, "", "")

    @patch("src.audio.separator.shutil.which", return_value="ffmpeg")
    def test_four_readable_stems_and_unique_jobs(self, _):
        with patch("src.audio.separator.subprocess.run", side_effect=self.produce):
            first = separate_audio(self.source, self.output, "htdemucs", False)
            second = separate_audio(self.source, self.output, "htdemucs", False)
        self.assertNotEqual(first, second)
        self.assertEqual(len(list(first.glob("*.wav"))), 4)

    @patch("src.audio.separator.shutil.which", return_value="ffmpeg")
    def test_incomplete_stems_are_not_success(self, _):
        def partial(command, **kwargs):
            result = self.produce(command, **kwargs)
            folder = Path(command[command.index("--out") + 1]) / "htdemucs" / self.source.stem
            (folder / "vocals.wav").unlink()
            return result
        with patch("src.audio.separator.subprocess.run", side_effect=partial):
            with self.assertRaises(Exception):
                separate_audio(self.source, self.output, "htdemucs", False)
        self.assertEqual(list(self.output.iterdir()), [])

    @patch("src.audio.separator.shutil.which", return_value="ffmpeg")
    def test_process_failure(self, _):
        with patch("src.audio.separator.subprocess.run", return_value=subprocess.CompletedProcess([], 1, "", "model error")):
            with self.assertRaisesRegex(RuntimeError, "model error"):
                separate_audio(self.source, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    @patch("src.audio.separator.shutil.which", return_value=None)
    def test_missing_ffmpeg(self, _):
        with self.assertRaisesRegex(RuntimeError, "FFmpeg"):
            separate_audio(self.source, self.output)

    def test_missing_input(self):
        with self.assertRaises(FileNotFoundError):
            separate_audio(self.root / "missing.wav", self.output)


class DownloadTests(unittest.TestCase):
    def test_invalid_url(self):
        with self.assertRaises(ValueError):
            AudioDownloader.download("https://youtube.com.example.org/video", "unused")

    @patch("src.core.downloader.shutil.which", return_value="ffmpeg")
    def test_requires_converted_file(self, _):
        with tempfile.TemporaryDirectory() as temp, patch("src.core.downloader.yt_dlp.YoutubeDL") as factory:
            client = factory.return_value.__enter__.return_value
            client.prepare_filename.return_value = str(Path(temp) / "test.webm")
            with self.assertRaisesRegex(RuntimeError, "MP3"):
                AudioDownloader.download("https://youtu.be/test", temp)
            (Path(temp) / "test.mp3").write_bytes(b"audio")
            self.assertEqual(AudioDownloader.download("https://youtu.be/test", temp), str(Path(temp) / "test.mp3"))
