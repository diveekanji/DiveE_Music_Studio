import hashlib
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from src.core import runtime_assets


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        mock_config = SimpleNamespace(base_path=self.root, app_data_path=self.root / "data")
        patcher = patch.object(runtime_assets, "config", mock_config)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_bundled_ffmpeg_works_with_empty_path_without_mutating_environment(self):
        binary_dir = self.root / "vendor" / "ffmpeg" / "bin"
        binary_dir.mkdir(parents=True)
        suffix = ".exe" if os.name == "nt" else ""
        for name in ("ffmpeg", "ffprobe"):
            (binary_dir / (name + suffix)).touch()
        with patch.dict(os.environ, {"PATH": ""}):
            env = runtime_assets.audio_environment()
            self.assertEqual(env["PATH"].split(os.pathsep)[0], str(binary_dir))
            self.assertEqual(os.environ["PATH"], "")
            self.assertTrue(Path(env["TEMP"]).is_dir())

    def test_missing_ffmpeg_fails_explicitly(self):
        with patch.object(runtime_assets.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "FFmpeg"):
                runtime_assets.ffmpeg_paths()

    def test_corrupted_checkpoint_rejected_before_model_loading(self):
        folder = self.root / "vendor" / "models"
        folder.mkdir(parents=True)
        checkpoint = folder / runtime_assets.MODEL_FILENAME
        checkpoint.write_bytes(b"test fixture")
        (folder / "htdemucs.yaml").write_text("models: ['955717e8']")
        with self.assertRaisesRegex(RuntimeError, "checksum"):
            runtime_assets.model_repository("htdemucs")
        with patch.object(runtime_assets, "MODEL_SHA256", hashlib.sha256(b"test fixture").hexdigest()):
            self.assertEqual(runtime_assets.model_repository("htdemucs"), folder)

    def test_missing_model_does_not_attempt_network_access(self):
        with self.assertRaisesRegex(RuntimeError, "model is missing"):
            runtime_assets.model_repository("htdemucs")
