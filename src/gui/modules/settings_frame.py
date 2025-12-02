import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path

from src.gui.shared import COLORS, ModernCard, PrimaryButton, SecondaryButton, ModernEntry, StatusBadge
from src.core.songsterr import SongsterrClient
from src.core.youtube import YouTubeUploader
from src.core.gmail import GmailClient

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, config_manager):
        super().__init__(parent, fg_color="transparent")
        self.config_manager = config_manager
        self.temp_config = config_manager.config.copy()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        ctk.CTkLabel(self.header, text="SETTINGS", font=("Roboto Medium", 24), text_color=COLORS["text_main"]).pack(side="left")
        
        # Content Scroll
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self._setup_general_section()
        self._setup_paths_section()
        self._setup_accounts_section()
        
        # Footer
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        
        self.btn_save = PrimaryButton(self.footer, text="Save All Settings", command=self.save_settings, color="success", width=150)
        self.btn_save.pack(side="right")

    def _setup_general_section(self):
        card = ModernCard(self.scroll_frame, title="General & Appearance")
        card.pack(fill="x", pady=(0, 20))
        inner = card.inner_frame

        # Theme
        ctk.CTkLabel(inner, text="App Theme:").grid(row=1, column=0, sticky="w", padx=20, pady=10)
        self.theme_var = ctk.StringVar(value=self.temp_config.get("theme", "Dark"))
        ctk.CTkOptionMenu(inner, values=["Dark", "Light", "System"], variable=self.theme_var).grid(row=1, column=1, sticky="w", padx=20)

        # Browser Behavior
        ctk.CTkLabel(inner, text="Browser Mode:").grid(row=2, column=0, sticky="w", padx=20, pady=10)
        self.var_headless = ctk.BooleanVar(value=self.temp_config.get("headless_browser", False))
        ctk.CTkCheckBox(inner, text="Headless (Hide Browser Window)", variable=self.var_headless).grid(row=2, column=1, sticky="w", padx=20)

        # Other Options
        self.var_keep_gp = ctk.BooleanVar(value=self.temp_config.get("keep_gp_file", True))
        ctk.CTkCheckBox(inner, text="Keep downloaded .gp files", variable=self.var_keep_gp).grid(row=3, column=1, sticky="w", padx=20, pady=10)
        
        self.var_open_folder = ctk.BooleanVar(value=self.temp_config.get("open_folder", True))
        ctk.CTkCheckBox(inner, text="Open output folder after process", variable=self.var_open_folder).grid(row=4, column=1, sticky="w", padx=20, pady=(0, 15))

    def _setup_paths_section(self):
        card = ModernCard(self.scroll_frame, title="Directories & Models")
        card.pack(fill="x", pady=(0, 20))
        inner = card.inner_frame

        # Splitter Output
        ctk.CTkLabel(inner, text="Splitter Output:").grid(row=1, column=0, sticky="w", padx=20, pady=(10,0))
        self.entry_split_out = ModernEntry(inner, width=300)
        self.entry_split_out.grid(row=2, column=0, sticky="ew", padx=20, pady=(5,10))
        self.entry_split_out.insert(0, self.temp_config.get("splitter_output_dir", ""))
        SecondaryButton(inner, text="Browse", command=lambda: self.browse_dir(self.entry_split_out)).grid(row=2, column=1, padx=10)

        # Tab Output
        ctk.CTkLabel(inner, text="Tab Output:").grid(row=3, column=0, sticky="w", padx=20, pady=(10,0))
        self.entry_tab_out = ModernEntry(inner, width=300)
        self.entry_tab_out.grid(row=4, column=0, sticky="ew", padx=20, pady=(5,10))
        self.entry_tab_out.insert(0, self.temp_config.get("tab_output_dir", ""))
        SecondaryButton(inner, text="Browse", command=lambda: self.browse_dir(self.entry_tab_out)).grid(row=4, column=1, padx=10)

        # TuxGuitar Path
        ctk.CTkLabel(inner, text="TuxGuitar.exe Path:").grid(row=5, column=0, sticky="w", padx=20, pady=(10,0))
        self.entry_tux = ModernEntry(inner, width=300)
        self.entry_tux.grid(row=6, column=0, sticky="ew", padx=20, pady=(5,15))
        self.entry_tux.insert(0, self.temp_config.get("tux_path", ""))
        SecondaryButton(inner, text="Browse", command=self.browse_exe).grid(row=6, column=1, padx=10)

        # Demucs Model
        ctk.CTkLabel(inner, text="AI Model (Demucs):").grid(row=7, column=0, sticky="w", padx=20, pady=(5,5))
        self.model_var = ctk.StringVar(value=self.temp_config.get("model", "htdemucs_6s"))
        ctk.CTkOptionMenu(inner, values=["htdemucs_6s", "htdemucs"], variable=self.model_var).grid(row=8, column=0, sticky="w", padx=20, pady=(0, 20))

    def _setup_accounts_section(self):
        card = ModernCard(self.scroll_frame, title="Account Integrations")
        card.pack(fill="x", pady=(0, 20))
        inner = card.inner_frame

        # Songsterr
        ctk.CTkLabel(inner, text="Songsterr (Plus):", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=20, pady=10)
        self.lbl_s_status = StatusBadge(inner, text="Checking...")
        self.lbl_s_status.grid(row=0, column=1, sticky="w", padx=10)
        
        # ▼▼▼ 修正箇所: command引数を追加 ▼▼▼
        self.btn_s_action = SecondaryButton(inner, text="Login", command=self.login_songsterr, width=100)
        self.btn_s_action.grid(row=0, column=2, padx=20)

        # Google
        ctk.CTkLabel(inner, text="Google (YT/Gmail):", font=("", 12, "bold")).grid(row=1, column=0, sticky="w", padx=20, pady=10)
        self.lbl_g_status = StatusBadge(inner, text="Checking...")
        self.lbl_g_status.grid(row=1, column=1, sticky="w", padx=10)
        
        # ▼▼▼ 修正箇所: command引数を追加 ▼▼▼
        self.btn_g_action = SecondaryButton(inner, text="Login", command=self.login_google, width=100)
        self.btn_g_action.grid(row=1, column=2, padx=20)

        self.update_account_ui()

    # --- Logic ---
    def browse_dir(self, entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def browse_exe(self):
        path = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if path:
            self.entry_tux.delete(0, "end")
            self.entry_tux.insert(0, path)

    def save_settings(self):
        new_conf = self.temp_config.copy()
        new_conf["theme"] = self.theme_var.get()
        new_conf["headless_browser"] = self.var_headless.get()
        new_conf["keep_gp_file"] = self.var_keep_gp.get()
        new_conf["open_folder"] = self.var_open_folder.get()
        new_conf["splitter_output_dir"] = self.entry_split_out.get()
        new_conf["tab_output_dir"] = self.entry_tab_out.get()
        new_conf["tux_path"] = self.entry_tux.get()
        new_conf["model"] = self.model_var.get()

        self.config_manager.save_config(new_conf)
        ctk.set_appearance_mode(new_conf["theme"])
        messagebox.showinfo("Saved", "Settings have been saved successfully.")

    def update_account_ui(self):
        if Path("songsterr_auth.json").exists():
            self.lbl_s_status.configure(text=" Active ", text_color=COLORS["success"])
            self.btn_s_action.configure(text="Logout", command=self.logout_songsterr, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
        else:
            self.lbl_s_status.configure(text=" Not logged in ", text_color="gray")
            self.btn_s_action.configure(text="Login", command=self.login_songsterr, fg_color="transparent")

        tokens = list(Path(".").glob("token_*.pickle"))
        if tokens:
            self.lbl_g_status.configure(text=" Active ", text_color=COLORS["success"])
            self.btn_g_action.configure(text="Logout", command=self.logout_google, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
        else:
            self.lbl_g_status.configure(text=" Not logged in ", text_color="gray")
            if Path("client_secrets.json").exists():
                self.btn_g_action.configure(text="Login", command=self.login_google, fg_color=COLORS["accent"], state="normal")
            else:
                self.lbl_g_status.configure(text="Missing client_secrets.json", text_color="orange")
                self.btn_g_action.configure(state="disabled")

    def login_songsterr(self):
        self.btn_s_action.configure(state="disabled", text="...")
        def _run():
            try:
                client = SongsterrClient(headless=False)
                client.login()
                self.after(0, lambda: messagebox.showinfo("Success", "Songsterr login saved."))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.after(0, self.update_account_ui)
        threading.Thread(target=_run, daemon=True).start()

    def logout_songsterr(self):
        if messagebox.askyesno("Confirm", "Remove Songsterr session?"):
            try:
                if Path("songsterr_auth.json").exists(): os.remove("songsterr_auth.json")
                self.update_account_ui()
            except: pass

    def login_google(self):
        self.btn_g_action.configure(state="disabled", text="...")
        def _run():
            try:
                yt = YouTubeUploader()
                yt.authenticate()
                gm = GmailClient()
                gm.authenticate()
                self.after(0, lambda: messagebox.showinfo("Success", "Google login saved."))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.after(0, self.update_account_ui)
        threading.Thread(target=_run, daemon=True).start()

    def logout_google(self):
        if messagebox.askyesno("Confirm", "Remove Google tokens?"):
            try:
                for f in Path(".").glob("token_*.pickle"): os.remove(f)
                self.update_account_ui()
            except: pass