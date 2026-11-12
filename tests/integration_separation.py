"""Opt-in real CPU inference: downloads the model on first use."""
import tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from src.audio.separator import separate_audio, STEMS


def main():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        time = np.arange(44100) / 44100
        signal = 0.1 * np.sin(2 * np.pi * 440 * time)
        source = root / "short.wav"
        sf.write(source, np.column_stack([signal, signal]), 44100)
        result = separate_audio(source, root / "output", "htdemucs", use_gpu=False)
        for stem in STEMS:
            info = sf.info(result / f"{stem}.wav")
            assert info.frames == 44100 and info.channels == 2, info
        print("PASS: real Demucs CPU inference produced four readable stereo WAV files.")


if __name__ == "__main__":
    main()
