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
