"""Fetch pinned Windows runtime assets; verify checksums before installation."""
import argparse
import hashlib
from importlib.metadata import distribution
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODEL_HASH = "8726e21a993978c7ba086d3872e7608d7d5bfca646ca4aca459ffda844faa8b4"
FFMPEG_HASH = "4705843ccaaf54257c16ad90f3e952ece33c17df964ecf7bfdbb0f49c7171077"
FFMPEG_URLS = [
    "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.7z",
    "https://github.com/GyanD/codexffmpeg/releases/download/9.0.2/ffmpeg-9.0.2-essentials_build.7z",
]
MODEL_URLS = [
    "https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/955717e8-8726e21a.th",
    "https://huggingface.co/deepvoice/svc/resolve/7138c6dda3e9c20fc160aa91130ba5c345e56322/955717e8-8726e21a.th",
]


def checksum(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download_verified(urls, destination, expected):
    destination = Path(destination)
    if destination.is_file() and checksum(destination) == expected:
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    errors = []
    for url in urls:
        try:
            print(f"Downloading {url}", flush=True)
            with urllib.request.urlopen(url, timeout=60) as response, partial.open("wb") as out:
                shutil.copyfileobj(response, out)
            if checksum(partial) != expected:
                raise ValueError("SHA-256 checksum mismatch")
            partial.replace(destination)
            return destination
        except (OSError, ValueError, urllib.error.URLError) as exc:
            partial.unlink(missing_ok=True)
            errors.append(f"{url}: {exc}")
    raise RuntimeError("Unable to obtain a verified asset:\n" + "\n".join(errors))


def prepare(cache):
    cache = Path(cache).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    model = download_verified(MODEL_URLS, cache / "htdemucs.th", MODEL_HASH)
    archive = download_verified(FFMPEG_URLS, cache / "ffmpeg-9.0.2.7z", FFMPEG_HASH)
    vendor = ROOT / "vendor"
    models = vendor / "models"
    models.mkdir(parents=True, exist_ok=True)
    shutil.copy2(model, models / f"955717e8-{MODEL_HASH}.th")
    (models / "htdemucs.yaml").write_text("models: ['955717e8']\n", encoding="utf-8")
    demucs = distribution("demucs")
    for file in demucs.files or []:
        if str(file).endswith(".dist-info/licenses/LICENSE"):
            shutil.copy2(demucs.locate_file(file), models / "LICENSE-Demucs.txt")
            break
    # Windows tar (libarchive) can extract 7z archives. Only a verified archive is used.
    with tempfile.TemporaryDirectory(dir=cache) as temp:
        subprocess.run(["tar", "-xf", str(archive), "-C", temp], check=True)
        extracted = Path(temp) / "ffmpeg-9.0.2-essentials_build"
        if not all((extracted / "bin" / f"{name}.exe").is_file() for name in ("ffmpeg", "ffprobe")):
            raise RuntimeError("FFmpeg archive is missing required executables")
        shutil.copytree(extracted, vendor / "ffmpeg", dirs_exist_ok=True)
    shutil.copy2(ROOT / "THIRD_PARTY_NOTICES.md", vendor / "THIRD_PARTY_NOTICES.md")
    print(f"Verified runtime assets installed in {vendor}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=ROOT / "data" / "asset-cache")
    prepare(parser.parse_args().cache)
