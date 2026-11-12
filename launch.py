"""Portable windowed launcher with a persistent startup log."""
import os
from pathlib import Path
import sys
import traceback


def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)
    logs = root / "data" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    with (logs / "application.log").open("a", encoding="utf-8", buffering=1) as log:
        sys.stdout = sys.stderr = log
        try:
            from main import DiveEMusicStudioApp
            app = DiveEMusicStudioApp()
            if "--smoke-test" in sys.argv:
                app.withdraw()
                app.update_idletasks()
                app.destroy()
                print("Portable GUI smoke test passed.")
            else:
                app.mainloop()
        except Exception:
            traceback.print_exc()
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, f"Could not start DiveE. See {logs / 'application.log'}", "DiveE Music Studio", 16)
            raise


if __name__ == "__main__":
    main()
