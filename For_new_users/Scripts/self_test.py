"""Offline packaged-app smoke test; never loads a real account or writes Notion."""
import json
from pathlib import Path
import tkinter as tk
from unittest.mock import patch


def run(report_path):
    import UI
    import ranking
    errors = []
    report = {'ok': False, 'errors': errors}
    import ssl
    import certifi
    from zoneinfo import ZoneInfo
    from datetime import datetime
    try:
        for zone in ('America/Los_Angeles', 'Europe/London', 'Asia/Tokyo'):
            assert datetime(2026, 1, 1, tzinfo=ZoneInfo(zone)).utcoffset() is not None
        report['timezone_data'] = 'passed'
        context = ssl.create_default_context(cafile=certifi.where())
        assert context.cert_store_stats()['x509_ca'] > 0
        report['tls_certificates'] = 'passed'
    except Exception as exc:
        errors.append(str(exc))
    config = {'user': 'Offline test', 'timezone': 'America/Los_Angeles',
              'all_users': {'Offline test': {'NOTION_TOKEN': 'offline', 'DATABASE_ID': 'offline'}}}
    def inspect(root):
        try:
            root.update_idletasks()
            if any(str(button['state']) == 'disabled' for button in UI.controls):
                raise RuntimeError('Startup worker did not release controls.')
            UI.social_media_entry.insert(0, '0')
            UI.time_focused_entry.insert(0, '600')
            if not 0 <= UI.get_values_from_user()['qol_score'] <= 100:
                raise RuntimeError('Form did not produce a valid score.')
            import onboarding
            import tempfile
            from group_setup import group_config
            with tempfile.TemporaryDirectory() as folder:
                invitation = {'format': 'qol-group', 'version': 1, 'group_name': 'Offline group',
                              'timezone': 'Europe/London', 'participants': [
                                  {'name': 'Alice', 'database_id': 'a'*32},
                                  {'name': 'Bob', 'database_id': 'b'*32}]}
                path = Path(folder) / 'invite.json'
                path.write_text(json.dumps(invitation))
                dialog = onboarding.GroupSetup(root)
                dialog.load_file(path)
                if dialog.name.get():
                    raise RuntimeError('Group setup must require an explicit identity selection.')
                dialog.name.set('Bob')
                dialog.token.set('offline-token')
                dialog.accept.set(True)
                with patch.object(onboarding, 'check_connections', return_value={}), patch.object(onboarding, 'save_config'):
                    dialog.finish()
                    root.wait_window(dialog.window)
                if dialog.result['user'] != 'Bob' or len(dialog.result['all_users']) != 2:
                    raise RuntimeError('Group onboarding failed to preserve the selected identity and full roster.')
                report['group_onboarding'] = 'passed'
                import threading
                entered = threading.Event()
                release = threading.Event()
                finished = threading.Event()
                def delayed_check(candidate):
                    entered.set()
                    release.wait(5)
                    finished.set()
                    return {}
                canceled = onboarding.GroupSetup(root)
                canceled.load_file(path)
                canceled.name.set('Alice')
                canceled.token.set('offline-token')
                canceled.accept.set(True)
                with patch.object(onboarding, 'check_connections', side_effect=delayed_check), patch.object(onboarding, 'save_config') as save:
                    canceled.finish()
                    if not entered.wait(2):
                        raise RuntimeError('Setup worker did not start.')
                    canceled.cancel()
                    release.set()
                    if not finished.wait(2):
                        raise RuntimeError('Canceled setup worker did not finish.')
                    root.update()
                    save.assert_not_called()
                    if canceled.result is not None:
                        raise RuntimeError('Canceled setup unexpectedly changed the account.')
                report['group_cancel_during_check'] = 'passed'
            rank_window = ranking.display_rankings({
                'scores': {'Alice': 90, 'Dan': 36.2, 'Erin': 50, 'Frank': 70},
                'dates': {'Alice': '2026-10-19', 'Dan': '2026-10-18'},
                'streaks': {'Alice': 4, 'Dan': -3, 'Erin': 0},
                'empty': ['Bob'], 'unavailable': {'Cathy': 'Offline'}}, parent=root)
            def find_table(widget):
                if isinstance(widget, ranking.ttk.Treeview):
                    return widget
                for child in widget.winfo_children():
                    found = find_table(child)
                    if found is not None:
                        return found
                return None
            table = find_table(rank_window)
            if table is None:
                raise RuntimeError('Ranking table did not render.')
            rows = {table.item(item, 'values')[1]: table.item(item, 'values') for item in table.get_children()}
            for name, expected in [('Alice', 'Good · 4'), ('Dan', 'Bad · 3'),
                                   ('Erin', 'No streak'), ('Frank', 'Unknown'), ('Bob', '—'), ('Cathy', '—')]:
                if rows[name][4] != expected:
                    raise RuntimeError('Incorrect streak display for ' + name)
            if rows['Dan'][2:4] != ('36.2', '2026-10-18'):
                raise RuntimeError('Ranking score/date changed while adding streaks.')
            report['ranking_streaks'] = 'passed'
            scoring_example = {'wake_time': '2026-10-20T08:30:00', 'sleep_time': '2026-10-20T23:30:00',
                               'todays_date': '2026-10-20', 'exercise': 'Yes', 'outside': 'Yes',
                               'talk': 'Yes', 'social_media': '0', 'time_focused': '495', 'offday_special_day': 'No'}
            for changes, expected in [({}, 95), ({'time_focused': '630', 'exercise': 'No'}, 97),
                                      ({'time_focused': '666', 'exercise': 'No', 'outside': 'No'}, 100),
                                      ({'time_focused': '700', 'sleep_time': '2026-10-20T23:31:00'}, 99.8)]:
                actual = UI.QOL_LIB.calculate_qol_score(dict(scoring_example, **changes))
                if abs(actual - expected) > 1e-8:
                    raise RuntimeError('Bundled two-route scoring or 11:30 PM bedtime is incorrect.')
            if not UI.build_default_datetime_strings()['sleep_time'].endswith('T23:30:00'):
                raise RuntimeError('Form bedtime does not default to 11:30 PM.')
            report['two_route_scoring'] = 'passed'
            report['ideal_bedtime'] = '23:30'
            UI.display_qol_score({'qol_score': 80, 'streak': 2})
            UI.display_analysis_results(root, 'Offline smoke test')
            ranking.display_it([('Offline test', 80)], parent=root)
            import matplotlib.pyplot as plt
            with patch.object(plt, 'show', side_effect=lambda: plt.close('all')):
                UI.plot_qol_score([('2026-10-19', 80), ('2026-10-20', 90)])
            root.update_idletasks()
            report['window_size'] = [root.winfo_width(), root.winfo_height()]
            report['screen_size'] = [root.winfo_screenwidth(), root.winfo_screenheight()]
            report['ok'] = not errors
        except Exception as exc:
            errors.append(str(exc))
        finally:
            root.destroy()
    try:
        with patch.object(UI, 'load_config', return_value=config), \
             patch.object(UI, 'get_highest_entry_number', return_value=0), \
             patch.object(UI.messagebox, 'showerror', side_effect=lambda *args, **kw: errors.append(str(args))):
            UI.main(on_ready=inspect)
    except Exception as exc:
        errors.append(str(exc))
    Path(report_path).write_text(json.dumps(report, indent=2))
    return 0 if report['ok'] else 1


def run_startup(report_path):
    """Exercise real first-run welcome with no account, plotting, or network."""
    import sys
    import time
    started = time.monotonic()
    import requests
    import UI
    from config import config_path
    report = {'ok': False, 'errors': []}
    if config_path().exists():
        report['errors'].append('Select a nonexistent QOL_CONFIG for the fresh-start test.')
        Path(report_path).write_text(json.dumps(report, indent=2))
        return 1
    def first_window(root):
        def inspect():
            try:
                welcome = next(w for w in root.winfo_children()
                               if isinstance(w, tk.Toplevel) and w.title() == 'Welcome to QOL Score')
                if not welcome.winfo_viewable():
                    raise RuntimeError('First-run welcome is not visible.')
                if 'matplotlib' in sys.modules:
                    raise RuntimeError('Plotting was imported before onboarding.')
                report.update(ok=True, welcome_visible=True, matplotlib_loaded=False,
                              seconds_to_welcome=round(time.monotonic() - started, 3))
                welcome.destroy()
            except Exception as exc:
                report['errors'].append(str(exc))
                root.destroy()
        root.after(250, inspect)
    try:
        with patch.object(requests.Session, 'request', side_effect=AssertionError('Startup must not use the network')):
            UI.main(on_window_ready=first_window)
    except Exception as exc:
        report['errors'].append(str(exc))
        report['ok'] = False
    Path(report_path).write_text(json.dumps(report, indent=2))
    return 0 if report['ok'] else 1
