"""Entry point for source launches and the self-contained macOS app."""
import faulthandler
import os
from pathlib import Path
import sys
import time
import traceback


def main():
    started = time.monotonic()
    support = Path.home() / 'Library' / 'Application Support' / 'QOL Score'
    log_stream = None
    def milestone(message):
        if log_stream:
            log_stream.write(f'{time.monotonic() - started:.3f}s {message}\n')
            log_stream.flush()
    try:
        support.mkdir(parents=True, exist_ok=True)
        log_stream = (support / 'startup.log').open('w', encoding='utf-8')
        os.chmod(support / 'startup.log', 0o600)
        milestone('Starting QOL Score 1.3.1')
        faulthandler.enable(file=log_stream)
        faulthandler.dump_traceback_later(30, file=log_stream)
        # PyInstaller's hook forces a temporary cache on every launch. This is
        # a one-folder app: keep the font cache in the user's writable support folder.
        if getattr(sys, 'frozen', False):
            os.environ['MPLCONFIGDIR'] = str(support / 'matplotlib')
        else:
            os.environ.setdefault('MPLCONFIGDIR', str(support / 'matplotlib'))
        if getattr(sys, 'frozen', False):
            # Conda's compiled TZPATH points into the developer's installation.
            # Use the explicitly bundled tzdata rather than any external path.
            import zoneinfo
            zoneinfo.reset_tzpath(())
        sys.path.insert(0, str(Path(__file__).resolve().parent / 'Scripts'))
        if len(sys.argv) == 3 and sys.argv[1] in ('--self-test', '--startup-test'):
            from self_test import run, run_startup
            faulthandler.cancel_dump_traceback_later()
            test = run if sys.argv[1] == '--self-test' else run_startup
            raise SystemExit(test(sys.argv[2]))
        milestone('Loading interface')
        from UI import main as start
        def ready(root):
            faulthandler.cancel_dump_traceback_later()
            milestone('First window displayed')
            def callback_error(kind, error, tb):
                milestone('Interface callback failed')
                detail = ''.join(traceback.format_exception(kind, error, tb))
                (support / 'last-error.log').write_text(detail, encoding='utf-8')
                from tkinter import messagebox
                messagebox.showerror('QOL Score', f'{error}\n\nDetails: {support / "last-error.log"}', parent=root)
            root.report_callback_exception = callback_error
        start(on_window_ready=ready)
        milestone('Closed normally')
    except Exception:
        detail = traceback.format_exc()
        milestone('Startup failed')
        try:
            (support / 'last-error.log').write_text(detail, encoding='utf-8')
        except OSError:
            pass
        from tkinter import Tk, messagebox
        root = Tk()
        root.withdraw()
        messagebox.showerror('QOL Score could not start',
            f'{detail.splitlines()[-1]}\n\nSee the error log at:\n{support / "last-error.log"}', parent=root)
        root.destroy()
        raise
    finally:
        faulthandler.cancel_dump_traceback_later()
        if log_stream:
            faulthandler.disable()
            log_stream.close()


if __name__ == '__main__':
    main()
