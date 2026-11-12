import unittest
from unittest.mock import patch


class StartupTests(unittest.TestCase):
    def test_app_constructs_all_screens_and_recovers_from_failure(self):
        from main import DiveEMusicStudioApp
        app = DiveEMusicStudioApp()
        app.withdraw()
        try:
            app.update_idletasks()
            self.assertEqual(app.studio_frame.transcribe_btn.cget("state"), "disabled")
            self.assertEqual(app.tools_frame.format_menu.cget("state"), "disabled")
            with patch("src.gui.modules.splitter.separate_audio", side_effect=RuntimeError("test failure")):
                app.splitter_frame._run_demucs_task("missing", "htdemucs", False)
            app.splitter_frame._poll_events()
            self.assertEqual(app.splitter_frame.btn_run.cget("state"), "normal")
            self.assertIn("ERROR", app.splitter_frame.status_badge.cget("text"))
            self.assertEqual(app.splitter_frame.progress_bar.get(), 0)
            with patch("src.gui.modules.tools.AudioDownloader.download", side_effect=RuntimeError("test failure")):
                app.tools_frame._download("https://youtu.be/test")
            app.tools_frame._poll_events()
            self.assertIn("failed", app.tools_frame.yt_status.cget("text"))
            self.assertEqual(app.tools_frame.yt_btn.cget("state"), "normal")
        finally:
            app.destroy()
