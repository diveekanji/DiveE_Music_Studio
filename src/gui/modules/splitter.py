# src/gui/modules/splitter.py

import os
import threading
import time
from pathlib import Path
import traceback
import demucs.api

import customtkinter as ctk
from tkinter import filedialog, END

# デザインシステム
from src.gui.shared import (
    ModernCard, PrimaryButton, SecondaryButton,
    SectionHeader, AppColors, AppFonts, StatusBadge
)

# パス管理（必須ルール）
from src.core.config_manager import config

# 実分離に使用
from demucs.api import Separator
from pydub import AudioSegment
import torch


class SplitterFrame(ctk.CTkFrame):
    def __init__(self, master, app_root, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app_root = app_root
        self.selected_file_path: str | None = None
        self.is_processing = False

        # レイアウト
        self.columnconfigure(0, weight=4)
        self.columnconfigure(1, weight=6)
        self.rowconfigure(0, weight=1)

        self._init_left_panel()
        self._init_right_panel()

    # ---------------- UI ----------------

    def _init_left_panel(self):
        self.left_panel = ModernCard(self)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        self.left_panel.grid_columnconfigure(0, weight=1)

        SectionHeader(self.left_panel, text="Input Source").pack(pady=(20, 10), padx=20, anchor="w")

        # ドロップゾーン（見た目はボタン）
        self.drop_zone = ctk.CTkButton(
            self.left_panel,
            text="\n📂\n\nDrag & Drop Audio File Here\nor Click to Browse",
            font=AppFonts.title(),
            fg_color="transparent",
            border_width=2,
            border_color=AppColors.SECONDARY,
            text_color=AppColors.TEXT_SUB,
            hover_color=AppColors.BG_HOVER,
            corner_radius=15,
            height=180,
            command=self._select_file_dialog
        )
        self.drop_zone.pack(fill="x", padx=20, pady=10)

        # DnD
        try:
            self.drop_zone.drop_target_register('DND_Files')
            self.drop_zone.dnd_bind('<<Drop>>', self._on_drop)
        except Exception:
            # tkinterdnd2が未初期化でも致命傷にしない
            pass

        # 選択ファイル表示
        self.file_label = ctk.CTkLabel(
            self.left_panel,
            text="No file selected",
            font=AppFonts.caption(),
            text_color=AppColors.TEXT_SUB,
            wraplength=300
        )
        self.file_label.pack(pady=(0, 20))

        # 設定
        SectionHeader(self.left_panel, text="Separation Settings").pack(pady=(10, 10), padx=20, anchor="w")

        self.model_var = ctk.StringVar(value="mdx_extra_q (High Quality)")
        self.model_combo = ctk.CTkOptionMenu(
            self.left_panel,
            values=["htdemucs (Standard)", "htdemucs_ft (Fine-tuned)", "mdx_extra_q (High Quality)"],
            variable=self.model_var,
            font=AppFonts.body(),
            fg_color=AppColors.BG_ROOT,
            button_color=AppColors.SECONDARY,
            button_hover_color=AppColors.PRIMARY,
            text_color=AppColors.TEXT_MAIN,
            corner_radius=8
        )
        self.model_combo.pack(fill="x", padx=20, pady=5)

        # GPU
        self.check_gpu = ctk.CTkSwitch(
            self.left_panel,
            text="Use GPU Acceleration (CUDA)",
            font=AppFonts.body(),
            progress_color=AppColors.PRIMARY,
            button_color=AppColors.TEXT_MAIN,
            button_hover_color="#E0E0E0"
        )
        self.check_gpu.pack(anchor="w", padx=20, pady=15)
        self.check_gpu.select()  # 既定ON

        # アクション
        self.action_area = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.action_area.pack(side="bottom", fill="x", padx=20, pady=20)

        self.btn_run = PrimaryButton(
            self.action_area,
            text="START SEPARATION",
            height=45,
            command=self._start_processing
        )
        self.btn_run.pack(fill="x")

    def _init_right_panel(self):
        self.right_panel = ModernCard(self)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        header_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)

        SectionHeader(header_frame, text="Console Output").pack(side="left")
        self.status_badge = StatusBadge(header_frame, status="READY", mode="info")
        self.status_badge.pack(side="right")

        # ログコンソール
        self.console = ctk.CTkTextbox(
            self.right_panel,
            font=AppFonts.code(),
            text_color="#00E676",
            fg_color="#0A0A0A",
            corner_radius=8,
            border_width=0
        )
        self.console.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.log("Welcome to DiveE Splitter. Ready to process.")

        # プログレス
        self.progress_bar = ctk.CTkProgressBar(
            self.right_panel, progress_color=AppColors.PRIMARY, height=8
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 20))

    # ---------------- Logic ----------------

    def _on_drop(self, event):
        file_path = event.data
        if isinstance(file_path, str) and file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        self._set_file(file_path)

    def _select_file_dialog(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav *.flac *.m4a"), ("All Files", "*.*")]
        )
        if file_path:
            self._set_file(file_path)

    def _set_file(self, path: str):
        self.selected_file_path = path
        filename = Path(path).name
        self.file_label.configure(text=f"Selected: {filename}", text_color=AppColors.PRIMARY)
        self.drop_zone.configure(border_color=AppColors.PRIMARY)
        self.log(f"File loaded: {path}")

    def log(self, message: str):
        def _write():
            timestamp = time.strftime("%H:%M:%S")
            self.console.configure(state="normal")
            self.console.insert(END, f"[{timestamp}] {message}\n")
            self.console.see(END)
            self.console.configure(state="disabled")
        self.after(0, _write)

    def _start_processing(self):
        if not self.selected_file_path:
            self.log("ERROR: Please select a file first.")
            self.status_badge.update_status("ERROR", "error")
            return
        if self.is_processing:
            return

        self.is_processing = True
        self.btn_run.configure(state="disabled", text="PROCESSING...")
        self.status_badge.update_status("RUNNING", "warning")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        threading.Thread(target=self._run_demucs_task, daemon=True).start()

    # --------------- Actual separation ---------------

    def _resolve_model_name(self, ui_name: str) -> str:
        mapping = {
            "htdemucs (Standard)": "htdemucs",
            "htdemucs_ft (Fine-tuned)": "htdemucs_ft",
            "mdx_extra_q (High Quality)": "mdx_extra_q",
        }
        return mapping.get(ui_name, "mdx_extra_q")

    def _ensure_wav(self, src_path: Path) -> Path:
        """
        Demucs は多くの形式を扱えますが、FFmpeg の有無に依存します。
        ここでは確実性のため WAV に変換してから渡します（pydub + ffmpeg）。
        """
        if src_path.suffix.lower() == ".wav":
            return src_path

        temp_dir = config.app_data_path / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        dst = temp_dir / (src_path.stem + ".wav")

        audio = AudioSegment.from_file(src_path)  # ffmpeg 必須
        audio.export(dst, format="wav")
        return dst

    def _output_root(self) -> Path:
        # すべて config_manager 経由（ルール厳守）
        out_root = config.app_data_path / "outputs" / "splitter"
        out_root.mkdir(parents=True, exist_ok=True)
        return out_root

    def _run_demucs_task(self):
        """
        実際に Demucs を叩いて分離し、出力フォルダへ保存する。
        """
        src = Path(self.selected_file_path)
        model_ui = self.model_var.get()
        model_name = self._resolve_model_name(model_ui)

        try:
            self.log(f"Starting separation using {model_name}...")
            self.log("-> Loading Model...")

            device = "cuda" if (self.check_gpu.get() and torch.cuda.is_available()) else "cpu"
            if device == "cpu" and self.check_gpu.get():
                self.log("!! CUDA not available. Falling back to CPU.")

            separator = Separator(model=model_name, device=device)

            self.log("-> Preparing Audio...")
            wav_path = self._ensure_wav(src)

            out_root = self._output_root()
            track_dir = out_root / src.stem  # 1曲ごとにサブフォルダ
            track_dir.mkdir(parents=True, exist_ok=True)

            self.log("-> Separating (this can take a while)...")
            # Demucs は destination にディレクトリを指定すると、{destination}/{filename}/ に書き出します
            separator.separate_audio_file(
                str(wav_path),
                destination=str(out_root),
                # ここでは4 stems (drums, bass, other, vocals) を標準出力
                # API 側に two-stems の指定は無いので、必要な場合は post-mix で対応
            )

            # 出力確認
            expected = [
                track_dir / "drums.wav",
                track_dir / "bass.wav",
                track_dir / "other.wav",
                track_dir / "vocals.wav",
            ]
            if not any(p.exists() for p in expected):
                # Demucs の一部モデルはサブディレクトリ名が変わる可能性があるため念のため探索
                maybe = list((out_root / src.stem).glob("*.wav"))
                if not maybe:
                    raise RuntimeError("No stems were written. Please check ffmpeg/torch install.")

            self.log("-> Finalizing...")
            self.status_badge.update_status("DONE", "success")
            self.log(f"Separation Complete! Files saved to: {track_dir}")

        except Exception as e:
            self.status_badge.update_status("ERROR", "error")
            self.log(f"ERROR: {e}")
            self.log(traceback.format_exc())
        finally:
            # UI 復帰
            self.after(0, lambda: self.btn_run.configure(state="normal", text="START SEPARATION"))
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(1.0)
            self.is_processing = False
