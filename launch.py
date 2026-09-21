"""Desktop entry point with a readable crash report for windowed builds."""
from release_info import VERSION
import sys
import traceback
from pathlib import Path


def launch():
    try:
        from main import main
        main()
    except Exception:
        import platform
        from datetime import datetime,timezone
        report=f'Applin Escape {VERSION} | {datetime.now(timezone.utc).isoformat()}\nPython {sys.version}\nPlatform {platform.platform()}\n\n'+traceback.format_exc()
        from model import default_save_dir
        folder=default_save_dir()
        folder.mkdir(parents=True,exist_ok=True)
        destination=folder/'last_error.txt'
        destination.write_text(report,encoding='utf-8')
        if sys.stderr: print(report,file=sys.stderr)
        try:
            from tkinter import Tk, messagebox
            root=Tk(); root.withdraw()
            messagebox.showerror('Applin Escape',f'The game stopped. Error details were saved to:\n{destination}')
            root.destroy()
        except Exception:
            pass
        raise SystemExit(1)


if __name__=='__main__': launch()
