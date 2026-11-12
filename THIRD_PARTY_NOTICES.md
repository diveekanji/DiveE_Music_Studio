# Bundled runtime components

This private portable build includes unmodified third-party components. Their own licenses apply; this file does not relicense the application.

## FFmpeg 9.0.2 essentials, Windows x64

- Builder: Gyan Doshi, https://www.gyan.dev/ffmpeg/builds/
- Archive: https://github.com/GyanD/codexffmpeg/releases/download/9.0.2/ffmpeg-9.0.2-essentials_build.7z
- SHA-256: `4705843ccaaf54257c16ad90f3e952ece33c17df964ecf7bfdbb0f49c7171077`
- Upstream source revision: https://github.com/FFmpeg/FFmpeg/commit/946fcce07b
- GPLv3. The original LICENSE, README, documentation, and binary configuration are retained in `vendor/ffmpeg/`. `ffmpeg -buildconf` prints the build configuration. Upstream build information and linked-library list: https://www.gyan.dev/ffmpeg/builds/#about-these-builds
- FFmpeg is executed as a separate program. No system installation or PATH modification is performed.

## Demucs / htdemucs

- Upstream: https://github.com/facebookresearch/demucs (MIT license).
- Official checkpoint identifier: https://github.com/facebookresearch/demucs/blob/v4.0.1/demucs/remote/files.txt
- Original checkpoint: https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/955717e8-8726e21a.th
- Pinned mirror: https://huggingface.co/deepvoice/svc/blob/7138c6dda3e9c20fc160aa91130ba5c345e56322/955717e8-8726e21a.th
- Full SHA-256: `8726e21a993978c7ba086d3872e7608d7d5bfca646ca4aca459ffda844faa8b4`
- The mirror's full SHA-256 matches the upstream checkpoint's published checksum prefix. Downloaded contents are checked against the pinned full digest before loading. TLS certificate verification remains enabled.
- Demucs license text is retained with the installed distribution in the portable runtime.

## Python and Python packages

The portable runtime contains CPython 3.11 and the packages recorded in `uv.lock`. Python's `LICENSE.txt`, package `*.dist-info` license files, and other included license files are retained. Python standalone builds: https://github.com/astral-sh/python-build-standalone
