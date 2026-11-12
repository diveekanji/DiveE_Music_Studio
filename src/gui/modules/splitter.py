# src/gui/modules/splitter.py

import queue
import threading
import time
from pathlib import Path
import traceback

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
from src.audio.separator import separate_audio


class SplitterFrame(ctk.CTkFrame):
    def __init__(self, master, app_root, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app_root = app_root
        self.selected_file_path: str | None = None
        self.is_processing = False
        self.events = queue.Queue()

        # レイアウト
        self.columnconfigure(0, weight=4)
        self.columnconfigure(1, weight=6)
        self.rowconfigure(0, weight=1)

        self._init_left_panel()
        self._init_right_panel()
        self.after(100, self._poll_events)

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

        self.model_var = ctk.StringVar(value="htdemucs (Bundled / Offline)")
        self.model_combo = ctk.CTkOptionMenu(
            self.left_panel,
            values=["htdemucs (Bundled / Offline)"],
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
        paths = self.tk.splitlist(event.data)
        if len(paths) != 1:
            self.log("Please drop one audio file at a time.")
            return
        self._set_file(paths[0])

    def _select_file_dialog(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav *.flac *.m4a"), ("All Files", "*.*")]
        )
        if file_path:
            self._set_file(file_path)

    def _set_file(self, path: str):
        if self.is_processing:
            return
        self.selected_file_path = path
        filename = Path(path).name
        self.file_label.configure(text=f"Selected: {filename}", text_color=AppColors.PRIMARY)
        self.drop_zone.configure(border_color=AppColors.PRIMARY)
        self.log(f"File loaded: {path}")

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.console.configure(state="normal")
        self.console.insert(END, f"[{timestamp}] {message}\n")
        self.console.see(END)
        self.console.configure(state="disabled")

    def _start_processing(self):
        if self.is_processing:
            return
        if not self.selected_file_path or not Path(self.selected_file_path).is_file():
            self.log("ERROR: Please select an existing audio file.")
            self.status_badge.update_status("ERROR", "error")
            return
        # Read Tk variables on the UI thread, before starting the worker.
        source = self.selected_file_path
        model = self.model_var.get().split()[0]
        use_gpu = bool(self.check_gpu.get())
        self.is_processing = True
        self.btn_run.configure(state="disabled", text="PROCESSING...")
        self.status_badge.update_status("RUNNING", "warning")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.log("Separating with the bundled model (no download). CUDA falls back to CPU when unavailable.")
        threading.Thread(target=self._run_demucs_task,
                         args=(source, model, use_gpu), daemon=True).start()

    def _run_demucs_task(self, source, model, use_gpu):
        try:
            output = separate_audio(source, config.app_data_path / "outputs" / "splitter",
                                    model=model, use_gpu=use_gpu)
            self.events.put((True, f"Separation complete: {output}"))
        except Exception:
            self.events.put((False, traceback.format_exc()))

    def _poll_events(self):
        try:
            while True:
                success, message = self.events.get_nowait()
                self.log(message)
                self.status_badge.update_status("DONE" if success else "ERROR",
                                                "success" if success else "error")
                self.progress_bar.stop()
                self.progress_bar.configure(mode="determinate")
                self.progress_bar.set(1 if success else 0)
                self.btn_run.configure(state="normal", text="START SEPARATION")
                self.is_processing = False
        except queue.Empty:
            pass
        self.after(100, self._poll_events)
