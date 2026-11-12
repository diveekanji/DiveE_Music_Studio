"""Demucs 4.0.1 CLI adapter; no GUI or model imports at application startup."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

MODELS = {"htdemucs", "htdemucs_ft", "mdx_extra"}
STEMS = ("drums", "bass", "other", "vocals")


def separate_audio(source, output_root, model="htdemucs", use_gpu=True):
    source = Path(source).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Audio file not found: {source}")
    if model not in MODELS:
        raise ValueError(f"Unsupported model: {model}")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg is required. Add ffmpeg and ffprobe to PATH.")

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    # A fresh directory prevents stale/partial output from being reported as success.
    job_dir = Path(tempfile.mkdtemp(prefix="separation-", dir=output_root))
    command = [sys.executable, "-m", "demucs.separate", "-n", model,
               "--out", str(job_dir), "--float32"]
    if not use_gpu:
        command += ["--device", "cpu"]
    # Demucs selects CUDA when available, otherwise CPU, if device is omitted.
    command.append(str(source))
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode:
            raise RuntimeError(f"Demucs failed ({result.returncode}):\n{result.stderr[-6000:]}")
        track_dir = job_dir / model / source.stem
        import soundfile as sf
        for stem in STEMS:
            info = sf.info(str(track_dir / f"{stem}.wav"))
            if info.frames <= 0 or info.samplerate <= 0:
                raise RuntimeError(f"Invalid stem output: {stem}")
        return track_dir
    except BaseException:
        shutil.rmtree(job_dir)
        raise
