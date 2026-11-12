"""Assemble a private Windows portable folder, preserving runtime license files."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def copy_file(source, target):
    """Support Windows long paths and resume interrupted copies without redoing large DLLs."""
    source, target = str(source), str(target)
    if os.name == "nt":
        if not source.startswith("\\\\?\\"):
            source = "\\\\?\\" + os.path.abspath(source)
        if not target.startswith("\\\\?\\"):
            target = "\\\\?\\" + os.path.abspath(target)
    if os.path.isfile(target):
        original, existing = os.stat(source), os.stat(target)
        if original.st_size == existing.st_size and original.st_mtime_ns == existing.st_mtime_ns:
            return target
    return shutil.copy2(source, target)


def build(python_home, site_packages, destination, resume=False):
    if destination.exists() and not resume:
        raise FileExistsError(f"Use a new output folder: {destination}")
    if not (ROOT / "vendor" / "models").is_dir() or not (ROOT / "vendor" / "ffmpeg" / "bin" / "ffmpeg.exe").is_file():
        raise RuntimeError("Run scripts/prepare_runtime.py first")
    destination.mkdir(parents=True, exist_ok=True)
    app = destination / "app"
    app.mkdir(exist_ok=True)
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
    for name in set(names):
        source = ROOT / name
        if source.is_file() and name != "DiveE_Source_Code.txt":
            target = app / name
            target.parent.mkdir(parents=True, exist_ok=True)
            copy_file(source, target)
    shutil.copytree(ROOT / "vendor", app / "vendor", dirs_exist_ok=True, copy_function=copy_file)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(python_home, destination / "runtime", dirs_exist_ok=True, ignore=ignore, copy_function=copy_file)
    shutil.copytree(site_packages, destination / "runtime" / "Lib" / "site-packages", dirs_exist_ok=True, ignore=ignore, copy_function=copy_file)
    (destination / "Start_DiveE.cmd").write_text(
        '@echo off\ncd /d "%~dp0"\nstart "" "%~dp0runtime\\pythonw.exe" "%~dp0app\\launch.py"\n',
        encoding="ascii")
    (destination / "はじめに.txt").write_text(
        "Start_DiveE.cmd をダブルクリックしてください。Python・FFmpeg のインストールは不要です。\n"
        "AI Splitter は標準モデルを同梱しているため、初回からオフラインで使えます。\n"
        "音声を選択して START SEPARATION を押してください。CPU では処理に時間がかかります。\n"
        "出力: app/data/outputs/splitter/\nログ: app/data/logs/application.log\n"
        "このフォルダ全体を一緒に移動してください。runtime や app/vendor を削除しないでください。\n"
        "YouTube ダウンロードのみネット接続が必要です。未実装機能は無効になっています。\n",
        encoding="utf-8-sig")
    print(f"Portable application: {destination}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-home", type=Path, required=True)
    parser.add_argument("--site-packages", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--resume", action="store_true", help="Resume a previously interrupted assembly of the same package")
    args = parser.parse_args()
    build(args.python_home.resolve(), args.site_packages.resolve(), args.destination.resolve(), args.resume)
