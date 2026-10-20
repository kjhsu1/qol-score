"""Rank current entry numbers consistently, including zero scores and ties."""
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from core import top_three
from notion_client import NotionClient


def retrieve_all_users_QOL(all_users):
    scores = {}
    for name, connection in all_users.items():
        if name == 'User_Analysis_Requests_Database':
            continue
        page = NotionClient(connection).latest()
        if page:
            scores[name] = page.get('properties', {}).get('QOL Score', {}).get('number')
    return scores


def get_top_three(scores):
    return top_three(scores)


def display_it(rank, parent=None):
    window = tk.Toplevel(parent) if parent else tk.Tk()
    window.title('Latest QOL Rankings')
    window.geometry('650x350')
    tk.Label(window, text='LATEST TOP 3', font=('Helvetica', 22, 'bold')).pack(pady=20)
    if not rank:
        tk.Label(window, text='No scores yet. Submit your first day to get started.').pack()
    for place, (name, score) in enumerate(rank, 1):
        tk.Label(window, text=f'{place}.  {name}    {score:g}', font=('Helvetica', 20)).pack(pady=8)
    tk.Label(window, text='Each person’s latest entry; dates may differ. Ties sort by name.').pack(pady=12)
    if parent is None:
        window.mainloop()
    return window


def main():
    from config import load_config
    config = load_config()
    if config is None:
        raise SystemExit('Open the main QOL Score app to configure your account first.')
    display_it(get_top_three(retrieve_all_users_QOL(config['all_users'])))


if __name__ == '__main__':
    main()
