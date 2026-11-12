"""Opt-in real CPU inference using only bundled FFmpeg and model assets."""
import os
import subprocess
import tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from src.audio.separator import separate_audio, STEMS
from src.core.runtime_assets import ffmpeg_paths, audio_environment


def main():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        time = np.arange(44100) / 44100
        signal = 0.1 * np.sin(2 * np.pi * 440 * time)
        source = root / "short.wav"
        sf.write(source, np.column_stack([signal, signal]), 44100)
        ffmpeg, _ = ffmpeg_paths()
        mp3 = root / "short.mp3"
        subprocess.run([str(ffmpeg), "-hide_banner", "-loglevel", "error", "-i", str(source), str(mp3)],
                       check=True, env=audio_environment(), capture_output=True)
        # Ensure the app never relies on a system FFmpeg or a remote model download.
        os.environ["PATH"] = ""
        os.environ["HTTP_PROXY"] = os.environ["HTTPS_PROXY"] = "http://127.0.0.1:9"
        for input_file in (source, mp3):
            result = separate_audio(input_file, root / "output", "htdemucs", use_gpu=False)
            for stem in STEMS:
                samples, rate = sf.read(result / f"{stem}.wav", always_2d=True)
                assert len(samples) == 44100 and samples.shape[1] == 2 and rate == 44100
                assert np.isfinite(samples).all()
            print(f"PASS: offline CPU separation of {input_file.suffix} produced four valid stereo WAV files.", flush=True)


if __name__ == "__main__":
    main()
