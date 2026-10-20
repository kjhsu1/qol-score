"""Rank all configured participants and identify incomplete results explicitly."""
import math
from core import top_three
from notion_client import NotionClient


def retrieve_rankings(all_users, client_factory=NotionClient):
    scores, dates, streaks, unavailable, empty = {}, {}, {}, {}, []
    for name, connection in all_users.items():
        if name == 'User_Analysis_Requests_Database':
            continue
        try:
            page = client_factory(connection).latest()
            props = page.get('properties', {}) if page else {}
            score = props.get('QOL Score', {}).get('number')
            if score is None:
                empty.append(name)
                continue
            if isinstance(score, bool) or not math.isfinite(float(score)) or not 0 <= float(score) <= 100:
                raise ValueError('Latest entry has an invalid score.')
            scores[name] = float(score)
            dates[name] = (props.get('Date', {}).get('date') or {}).get('start', '')[:10]
            streaks[name] = (props.get('Streak') or {}).get('number')
        except Exception as exc:
            unavailable[name] = str(exc).replace(connection['NOTION_TOKEN'], '[token hidden]')
    return {'scores': scores, 'dates': dates, 'streaks': streaks, 'unavailable': unavailable, 'empty': empty}


def retrieve_all_users_QOL(all_users):
    # Compatibility API: callers needing completeness should use retrieve_rankings.
    return retrieve_rankings(all_users)['scores']


def get_top_three(scores):
    return top_three(scores)


def format_streak(value):
    """Use the signed streak saved on the same entry as the displayed score."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 'Unknown'
    if not math.isfinite(value) or value != int(value):
        return 'Unknown'
    count = int(value)
    if count > 0:
        return f'Good · {count}'
    if count < 0:
        return f'Bad · {abs(count)}'
    return 'No streak'


def display_it(rank, parent=None, details=None):
    import tkinter as tk
    from tkinter import ttk
    window = tk.Toplevel(parent) if parent else tk.Tk()
    window.title('QOL Group Rankings')
    window.geometry('850x480')
    frame = ttk.Frame(window, padding=15)
    frame.pack(fill='both', expand=True)
    incomplete = bool(details and details['unavailable'])
    ttk.Label(frame, text='PARTIAL RANKINGS — some connections failed' if incomplete else 'LATEST RANKINGS',
              font=('Helvetica', 18, 'bold')).pack(pady=10)
    table_frame = ttk.Frame(frame)
    table_frame.pack(fill='both', expand=True)
    table = ttk.Treeview(table_frame, columns=('rank', 'name', 'score', 'date', 'streak'), show='headings')
    for key, label, width in [('rank', 'Rank', 55), ('name', 'Participant', 220), ('score', 'Score', 85), ('date', 'Entry date', 130), ('streak', 'Current streak', 150)]:
        table.heading(key, text=label); table.column(key, width=width)
    scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=table.yview)
    table.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right', fill='y'); table.pack(fill='both', expand=True)
    for place, (name, score) in enumerate(rank, 1):
        table.insert('', 'end', values=(place, name, f'{score:g}', (details or {}).get('dates', {}).get(name, ''),
                                        format_streak((details or {}).get('streaks', {}).get(name))))
    if details:
        for name in details['empty']:
            table.insert('', 'end', values=('—', name, 'No score', '', '—'))
        for name in details['unavailable']:
            table.insert('', 'end', values=('—', name, 'Unavailable', '', '—'))
    if not rank and not details:
        ttk.Label(frame, text='No scores yet. Submit your first day to get started.').pack()
    if incomplete:
        ttk.Label(frame, text='Unavailable: ' + ', '.join(details['unavailable']) + '. Ask the organizer to check access, then retry.',
                  foreground='#a00000', wraplength=670).pack(pady=8)
    ttk.Label(frame, text='Each person’s latest numbered entry; dates may differ. Ties sort by name.', wraplength=670).pack(pady=8)
    ttk.Label(frame, text='Good: score ≥65. Bad: score <65. Streak counts recorded entries, not calendar days.', wraplength=800).pack(pady=4)
    if parent is None:
        window.mainloop()
    return window


def display_rankings(details, parent=None):
    rank = sorted(details['scores'].items(), key=lambda row: (-row[1], row[0].casefold()))
    return display_it(rank, parent, details)


def main():
    from config import load_config
    config = load_config()
    if config is None:
        raise SystemExit('Open the main QOL Score app to configure your account first.')
    display_rankings(retrieve_rankings(config['all_users']))


if __name__ == '__main__':
    main()
