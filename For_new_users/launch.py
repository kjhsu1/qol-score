"""Entry point for source launches and the self-contained macOS app."""
import os
from pathlib import Path
import sys
import traceback


def main():
    support = Path.home() / 'Library' / 'Application Support' / 'QOL Score'
    support.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR', str(support / 'matplotlib'))
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'Scripts'))
    try:
        if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
            from self_test import run
            raise SystemExit(run(sys.argv[2]))
        from UI import main as start
        start()
    except Exception:
        log = support / 'last-error.log'
        log.write_text(traceback.format_exc())
        from tkinter import Tk, messagebox
        root = Tk()
        root.withdraw()
        messagebox.showerror('QOL Score could not start', f'See the error log at:\n{log}', parent=root)
        root.destroy()
        raise


if __name__ == '__main__':
    main()
