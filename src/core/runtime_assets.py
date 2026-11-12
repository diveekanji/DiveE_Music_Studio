"""Resolve bundled binaries and a verified local model without changing system PATH."""
import hashlib
import os
from pathlib import Path
import shutil

from src.core.config_manager import config

MODEL_SHA256 = "8726e21a993978c7ba086d3872e7608d7d5bfca646ca4aca459ffda844faa8b4"
MODEL_FILENAME = f"955717e8-{MODEL_SHA256}.th"


def ffmpeg_paths():
    bundled = config.base_path / "vendor" / "ffmpeg" / "bin"
    suffix = ".exe" if os.name == "nt" else ""
    paths = [bundled / f"{name}{suffix}" for name in ("ffmpeg", "ffprobe")]
    if all(path.is_file() for path in paths):
        return tuple(paths)
    system = [shutil.which(name) for name in ("ffmpeg", "ffprobe")]
    if all(system):
        return tuple(Path(path) for path in system)
    raise RuntimeError("Bundled FFmpeg is missing. Run scripts/prepare_runtime.py or restore the portable package.")


def audio_environment():
    ffmpeg, ffprobe = ffmpeg_paths()
    env = os.environ.copy()
    folders = dict.fromkeys((str(ffmpeg.parent), str(ffprobe.parent)))
    env["PATH"] = os.pathsep.join([*folders, env.get("PATH", "")])
    env["PYTHONIOENCODING"] = "utf-8"
    # Demucs uses temporary files; keep them in the app's writable data directory.
    temp = config.app_data_path / "temp"
    temp.mkdir(parents=True, exist_ok=True)
    env["TEMP"] = env["TMP"] = str(temp)
    return env


def model_repository(model):
    if model != "htdemucs":
        raise ValueError("This portable release supports the bundled htdemucs model.")
    folder = config.base_path / "vendor" / "models"
    checkpoint = folder / MODEL_FILENAME
    if not checkpoint.is_file() or not (folder / "htdemucs.yaml").is_file():
        raise RuntimeError("Bundled model is missing. Run scripts/prepare_runtime.py or restore the portable package.")
    with checkpoint.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != MODEL_SHA256:
        raise RuntimeError("Model checksum mismatch. Restore the original portable package.")
    return folder
