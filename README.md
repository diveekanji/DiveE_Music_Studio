# DiveE Music Studio

音源分離と音声ダウンロードのデスクトップアプリです。現在は開発版で、表示されるすべての機能が完成しているわけではありません。

## 対応状況

| 機能 | 状態 | 備考 |
| --- | --- | --- |
| AI Splitter | 実装済み | Demucs 4.0.1 で drums / bass / other / vocals を WAV 保存。4ファイルを読み取り確認してから完了表示 |
| YouTube → MP3 | 実装済み・外部サービス依存 | yt-dlp + FFmpeg。変換後のファイルが存在する場合のみ成功表示。サイト変更・認証・通信状態によって失敗する場合あり |
| Tab Studio | 未接続・操作無効 | 採譜、URL 取り込み、TuxGuitar 起動は実行しません |
| Format Converter / BPM・Key | 未実装・操作無効 | コアの試作処理はありますが画面からは使えません |
| Settings | 一部実装 | 保存先表示、データフォルダを開く、テーマ変更。キャッシュ削除は無効。テーマの永続保存なし |

## 必要な環境

- 対応基準: Windows x64、Python **3.11**、デスクトップ画面が使える環境。
- [uv](https://docs.astral.sh/uv/getting-started/installation/) をインストールしてください。
- [FFmpeg](https://ffmpeg.org/download.html) の Windows ビルドを展開し、`ffmpeg.exe` と `ffprobe.exe` がある `bin` を PATH に追加してください。
- GPU は必須ではありません。CUDA が利用できない場合は CPU を使用します。GPU 用の Torch 構成はこのリリースの検証対象外です。
- 初回の依存関係取得とモデルダウンロードにはネット接続・空きディスク容量が必要です。CPU での分離には時間がかかります。
- macOS / Linux と実行ファイル配布は未検証です。PyInstaller は依存関係にありますが、ビルド仕様・配布物はまだ提供していません。

## 起動（PowerShell）

```powershell
git clone https://github.com/diveekanji/DiveE_Music_Studio.git
cd DiveE_Music_Studio
uv python install 3.11
uv sync --locked
ffmpeg -version
ffprobe -version
uv run --locked python main.py
```

`uv.lock` は再現可能な環境構築のために管理しています。Python 3.12 以降は現在の対応範囲に含めていません。
Windows で依存パッケージの構築中に長いパスのエラーが発生する場合は、リポジトリと `UV_CACHE_DIR` を短いパスに配置して再試行してください。

## 操作と保存先

AI Splitter で音声を1件選び、モデルを選択して START SEPARATION を押します。GPU の選択を外すと CPU に固定できます。
標準モデルは `htdemucs` です。未導入の DiffQ を必要とする `mdx_extra_q` は選択肢から外し、`mdx_extra` を使用します。
結果は `data/outputs/splitter/separation-<一意のID>/<モデル名>/<曲名>/` に保存されます。同名の曲を再実行しても前回の結果を上書きしません。失敗した実行の部分的な出力は削除します。

Tools に YouTube URL を入力すると `data/outputs/downloads/` に MP3 を保存します。曲名に動画 ID を含め、異なる動画の同名衝突を抑えています。
処理中のキャンセルは未実装です。分離やダウンロードが完了するまでアプリを終了しないでください。

開発時のデータはリポジトリ内の `data/` にあります。モデル重みは Demucs / Torch 標準のキャッシュを使います。Settings の Models Path はアプリ側の予約領域で、Demucs のダウンロード先ではありません。
PyInstaller 用のパス分岐は `src/core/config_manager.py` にありますが、配布ビルドの動作保証を意味しません。

## 検証

```powershell
uv run --locked python -m unittest discover -s tests -v
uv run --locked python -m demucs.separate --help
# 実モデルを取得して短い合成音声を CPU で分離する任意の統合テスト
uv run --locked python -m tests.integration_separation
```

通常テストは GUI の生成、失敗時の操作復帰、CLI 引数、4つの出力の検証、欠落出力・外部プロセス失敗・FFmpeg 不在、ダウンロード成果物の確認を扱います。外部処理はモック化し、通常テストではモデル取得や YouTube 接続を行いません。実推論は上記の統合テストで別途確認します。
GitHub Actions は Windows で通常テストと Demucs CLI の読み込みを実行します。

今回のローカル検証では Windows / Python 3.11 で依存関係の導入、8件の通常テスト、Demucs CLI の読み込みが成功しました。実モデルの統合テストは、重みの配布元 `dl.fbaipublicfiles.com` の証明書期限切れによってダウンロード段階で停止しています。実推論、実際の YouTube ダウンロード、GPU は未検証です。証明書の検証を無効化せず、配布元の復旧後に統合テストを実行してください。

## ソースと今後の作業

- `main.py` → `src/gui/modules/{splitter,tab_studio,tools,settings}.py` が正規の画面です。重複していた `*_frame.py` は削除しました。以前の実装は Git 履歴から参照できます。
- `src/audio/separator.py` は Demucs CLI との接続と成果物検証を担当します。重いモデルを画面起動時に読み込みません。
- `src/audio/transcriber.py`、Songsterr / Gmail / YouTube アップロード / TuxGuitar 関連は未接続の試作コードです。採譜の `basic_pitch` は現行依存関係に含まず、起動時にも読み込みません。有効化前に互換性のある依存構成と統合テストを追加してください。
- `DiveE_Source_Code.txt` は過去のソース書き出しで、現行ソースの正本ではありません。変更・レビューには個別の `.py` を使用してください。

次の開発候補は、採譜機能の依存関係を分離して接続すること、長時間処理のキャンセルと終了処理、配布ビルドの整備です。
