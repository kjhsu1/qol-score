"""Regressions for dependencies hidden by a developer's existing Mac setup."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'For_new_users' / 'Scripts'))
from config import backup_config, load_config, save_config, validate_config


def account():
    return {'user': 'Alice', 'timezone': 'Asia/Tokyo',
            'all_users': {'Alice': {'NOTION_TOKEN': 'offline', 'DATABASE_ID': 'a'*32}}}


class PortabilityTests(unittest.TestCase):
    def test_ui_import_does_not_depend_on_plotting_or_network(self):
        code = '''
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('matplotlib', 'numpy'):
            raise AssertionError('Plotting must not block startup: ' + fullname)
sys.meta_path.insert(0, Block())
import requests
requests.Session.request = lambda *a, **k: (_ for _ in ()).throw(AssertionError('network'))
import UI
assert not hasattr(UI, 'root')
'''
        env = dict(os.environ, PYTHONPATH=str(ROOT/'For_new_users'/'Scripts'))
        result = subprocess.run([sys.executable, '-c', code], env=env, cwd='/private/tmp',
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_timezone_data_without_system_database(self):
        code = '''
from zoneinfo import ZoneInfo
from datetime import datetime
assert datetime(2026, 7, 1, tzinfo=ZoneInfo('America/Los_Angeles')).utcoffset().total_seconds() == -25200
assert datetime(2026, 1, 1, tzinfo=ZoneInfo('Europe/London')).utcoffset().total_seconds() == 0
assert datetime(2026, 1, 1, tzinfo=ZoneInfo('Asia/Tokyo')).utcoffset().total_seconds() == 32400
'''
        result = subprocess.run([sys.executable, '-c', code], env=dict(os.environ, PYTHONTZPATH=''),
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_malformed_settings_are_rejected_before_client_construction(self):
        for bad in [[], None, {'all_users': []},
                    dict(account(), user=[]), dict(account(), user=' Alice '),
                    dict(account(), all_users={'Alice': {'NOTION_TOKEN': 12, 'DATABASE_ID': 'a'*32}}),
                    dict(account(), all_users={'Alice': {'NOTION_TOKEN': 'token', 'DATABASE_ID': None}})]:
            with self.subTest(config=bad):
                with self.assertRaises(ValueError):
                    validate_config(bad)

    def test_backup_preserves_invalid_bytes_and_allows_fresh_setup(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'settings 日本語.json'
            path.write_bytes(b'\xffbroken')
            with self.assertRaises(ValueError): load_config(path)
            backup = backup_config(path)
            self.assertEqual(backup.read_bytes(), b'\xffbroken')
            self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
            self.assertIsNone(load_config(path))
            save_config(account(), path)
            self.assertEqual(load_config(path), account())
            self.assertEqual(backup.read_bytes(), b'\xffbroken')

    def test_failed_atomic_save_keeps_original_and_cleans_temporary(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'config.json'
            save_config(account(), path)
            original = path.read_bytes()
            updated = dict(account(), timezone='Europe/London')
            with patch('config.os.replace', side_effect=OSError('disk full')):
                with self.assertRaises(OSError): save_config(updated, path)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_independent_saves_do_not_share_temporary_files(self):
        with tempfile.TemporaryDirectory() as folder:
            from concurrent.futures import ThreadPoolExecutor
            path = Path(folder) / 'config.json'
            variants = [dict(account(), timezone=zone) for zone in
                        ('Asia/Tokyo', 'Europe/London', 'America/Los_Angeles')]
            with ThreadPoolExecutor(max_workers=3) as executor:
                list(executor.map(lambda candidate: save_config(candidate, path), variants))
            self.assertIn(load_config(path), variants)
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_offline_startup_releases_controls_and_keeps_form(self):
        import UI
        import requests
        from unittest.mock import Mock
        import threading
        done = threading.Event()
        UI.controls = [Mock() for _ in range(5)]
        for button in UI.controls: button.__getitem__ = Mock(return_value='normal')
        UI.root = Mock()
        UI.status_var = Mock()
        UI.user = 'Alice'
        UI.config = account()
        callbacks = []
        UI.root.after.side_effect = lambda delay, callback: callbacks.append(callback)
        def offline():
            done.set()
            raise requests.ConnectionError('offline')
        try:
            with patch.object(UI.messagebox, 'showerror') as error:
                success = Mock()
                UI.run_async(offline, success)
                self.assertTrue(done.wait(2))
                # Synchronize via queue polling, as the UI does, without a Tk session.
                import time
                deadline = time.monotonic() + 2
                while callbacks and not error.called and time.monotonic() < deadline:
                    callbacks.pop(0)()
                error.assert_called_once()
                success.assert_not_called()
                for button in UI.controls: button.config.assert_called_with(state='normal')
        finally:
            for name in ('root', 'controls', 'status_var', 'user', 'config'):
                delattr(UI, name)


if __name__ == '__main__':
    unittest.main()
