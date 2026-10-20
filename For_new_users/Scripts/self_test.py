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
            ranking.display_rankings({'scores': {'Alice': 90}, 'dates': {'Alice': '2026-10-19'},
                                      'empty': ['Bob'], 'unavailable': {'Cathy': 'Offline'}}, parent=root)
            UI.display_qol_score({'qol_score': 80, 'streak': 2})
            UI.display_analysis_results(root, 'Offline smoke test')
            ranking.display_it([('Offline test', 80)], parent=root)
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
             patch.object(UI.messagebox, 'showerror', side_effect=lambda *args, **kw: errors.append(str(args))), \
             patch.object(UI.plt, 'show', side_effect=lambda: UI.plt.close('all')):
            UI.main(on_ready=inspect)
    except Exception as exc:
        errors.append(str(exc))
    Path(report_path).write_text(json.dumps(report, indent=2))
    return 0 if report['ok'] else 1
