# DiveE Music Studio

音源分離と音声ダウンロードの Windows デスクトップアプリです。開発版のため、未実装機能は画面上で無効化しています。

## 同梱版の起動

`DiveE_Music_Studio_Portable/Start_DiveE.cmd` をダブルクリックしてください。
Python、FFmpeg、ffprobe、標準の音源分離モデル htdemucs を含みます。インストール、PATH 設定、初回のモデルダウンロードは不要です。
フォルダ全体を一緒に移動できます。`runtime` と `app/vendor` を削除しないでください。

AI Splitter で音声を1件選び、START SEPARATION を押します。標準モデルで drums / bass / other / vocals の4種類に分離します。初回からオフラインで使えます。CPU での処理には時間がかかります。
YouTube ダウンロードのみインターネット接続が必要です。

## 対応状況

| 機能 | 状態 | 備考 |
| --- | --- | --- |
| AI Splitter | 実装済み | Demucs 4.0.1 + 同梱 htdemucs。4ファイルを読み取り確認してから完了表示 |
| YouTube → MP3 | 実装済み・外部サービス依存 | yt-dlp と同梱 FFmpeg を使用。変換済みファイルの存在確認後に成功表示 |
| Tab Studio | 未接続・操作無効 | 採譜、URL 取り込み、TuxGuitar 起動は実行しません |
| Format Converter / BPM・Key | 未実装・操作無効 | コアの試作処理は画面に未接続 |
| Settings | 一部実装 | 同梱ファイル・保存先表示、フォルダを開く、テーマ変更。テーマの永続保存とキャッシュ削除は未実装 |

対応基準は Windows x64 / Python 3.11 です。同梱版は Python 3.11.18、FFmpeg 9.0.2 を使用します。
CUDA が利用できない場合は CPU を使用します。GPU 用 Torch 構成、macOS / Linux、インストーラーは未検証です。
同梱版は Python 実行環境を含むフォルダ形式で、単一の exe ではありません。

## 保存先とログ

- 同梱版の分離結果: `app/data/outputs/splitter/separation-<一意のID>/htdemucs/<曲名>/`
- 同梱版のダウンロード: `app/data/outputs/downloads/`
- 同梱版の起動ログ: `app/data/logs/application.log`
- ソースから起動する場合は `app/` を除いた同じ相対パスです。

同名曲の分離を再実行しても、前回の結果は上書きしません。失敗した実行の部分出力は削除します。
処理のキャンセルは未実装です。完了までアプリを終了しないでください。

## ソースから起動（開発者向け）

リポジトリには大きなバイナリをコミットせず、固定 URL と SHA-256 を使う準備スクリプトを管理しています。同梱フォルダには取得済みの実ファイルを含めます。

```powershell
git clone https://github.com/diveekanji/DiveE_Music_Studio.git
cd DiveE_Music_Studio
# PR の変更を使う場合
git switch codex/stabilize-music-studio
uv python install 3.11
uv sync --locked
uv run --locked python scripts/prepare_runtime.py
uv run --locked python main.py
```

[uv の導入手順](https://docs.astral.sh/uv/getting-started/installation/)。準備スクリプトは Windows 標準の `tar.exe` を使用します。
Windows で長いパスによるパッケージ構築エラーが起きる場合は、リポジトリと `UV_CACHE_DIR` を短いパスに配置してください。

FFmpeg の配布アーカイブとモデルの SHA-256 を検証してから `vendor/` に配置します。モデルは公式配布元が失敗した場合、コミットを固定したミラーから取得し、同じ完全な SHA-256 を照合します。TLS 証明書の検証は無効化しません。
分離処理は `--repo` で同梱モデルを指定するため、実行時にリモート配布元へアクセスしません。同梱モデルが欠落・破損した場合は、ネット取得へ切り替えずエラーを表示します。
標準 htdemucs のみ対応します。追加モデルはこの同梱版の選択肢に含めていません。

## 検証

```powershell
uv run --locked python -m unittest discover -s tests -v
uv run --locked python -m demucs.separate --help
# 同梱ファイルの準備後、実モデルで WAV と MP3 を分離
uv run --locked python -m tests.integration_separation
```

通常テストは GUI 起動と失敗時復帰、CLI 引数、成果物、FFmpeg 不在、同梱優先と環境変数の非破壊、モデル破損・欠落を検証します。
実分離の統合テストは、システム PATH を空にし、ネット接続を使えないプロキシ設定で実行します。同梱 FFmpeg による MP3 変換と、WAV / MP3 からそれぞれ4種類の読み取り可能なステレオ WAV が出ることを確認します。これは音楽的な分離品質を評価するテストではありません。
GitHub Actions は Windows で通常テストと Demucs CLI の読み込みを実行します。実モデルの統合テストは任意実行です。

2026-11-12 のローカル検証で、12件の通常テストと、同梱モデルによる WAV / MP3 の実分離が成功しました。実際の YouTube ダウンロードと GPU 実行は未検証です。

## 同梱フォルダの再構築

準備済み `vendor/`、Python standalone の展開先、`uv sync --locked` 済み環境を渡します。

```powershell
uv run --locked python scripts/build_portable.py --python-home C:/build/python --site-packages .venv/Lib/site-packages --destination C:/build/DiveE_Music_Studio_Portable
```

新しい出力フォルダを指定してください。Python と依存パッケージのライセンス、FFmpeg 配布物のライセンス・文書を保持します。配布元と検証値は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) にあります。

## ソースの構成

- `main.py` と `src/gui/modules/{splitter,tab_studio,tools,settings}.py` が正規の画面です。
- `src/audio/separator.py` は別プロセスで Demucs CLI を実行し、出力を検証します。
- `src/core/runtime_assets.py` は同梱 FFmpeg とモデルを解決します。システムの PATH は変更しません。
- `src/audio/transcriber.py`、Songsterr / Gmail / YouTube アップロード / TuxGuitar 関連は未接続の試作です。採譜の `basic_pitch` は現行依存関係に含まず、起動時にも読み込みません。
- 重複していた `*_frame.py` は削除し、以前の実装は Git 履歴に残しています。
- `DiveE_Source_Code.txt` は過去の書き出しで、現行ソースの正本ではありません。

次の候補は採譜の接続、長時間処理のキャンセル、インストーラーの整備です。
