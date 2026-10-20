"""Guided setup for trusted groups sharing one master Notion workspace."""
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from group_setup import read_invitation, group_config, check_connections, make_invitation
from config import save_config


class GroupSetup:
    def __init__(self, parent, existing=None):
        self.result = None
        self.invitation = None
        self.existing = existing or {}
        self.busy = False
        self.closed = False
        self.poll_id = None
        self.window = tk.Toplevel(parent)
        self.window.title('Join your QOL group')
        self.window.geometry('680x580')
        self.window.transient(parent)
        self.window.protocol('WM_DELETE_WINDOW', self.cancel)
        frame = ttk.Frame(self.window, padding=20)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Join your QOL group', font=('Helvetica', 20, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='The organizer keeps one database per person in the master Notion account.\nImport their invitation, then choose your name.', wraplength=620).pack(anchor='w', pady=10)
        self.import_button = ttk.Button(frame, text='1. Import group invitation…', command=self.choose_file)
        self.import_button.pack(anchor='w')
        self.summary = tk.StringVar(value='No invitation selected.')
        ttk.Label(frame, textvariable=self.summary, wraplength=620).pack(anchor='w', pady=8)
        ttk.Label(frame, text='2. Your name — entries will be saved to this person’s database').pack(anchor='w')
        self.name = tk.StringVar()
        self.names = ttk.Combobox(frame, textvariable=self.name, state='readonly')
        self.names.pack(fill='x', pady=5)
        ttk.Label(frame, text='3. Group Notion token — get it privately from the organizer').pack(anchor='w')
        self.token = tk.StringVar()
        self.token_entry = ttk.Entry(frame, textvariable=self.token, show='•')
        self.token_entry.pack(fill='x', pady=5)
        ttk.Label(frame, text='4. Your timezone (for example America/Los_Angeles)').pack(anchor='w')
        self.timezone = tk.StringVar(value=self.existing.get('timezone', 'America/Los_Angeles'))
        self.timezone_entry = ttk.Entry(frame, textvariable=self.timezone)
        self.timezone_entry.pack(fill='x', pady=5)
        self.accept = tk.BooleanVar(value=False)
        self.accept_button = ttk.Checkbutton(frame, variable=self.accept,
            text='This is a trusted group. The token can read everyone’s data, including diaries,\nand can insert entries in every connected database.')
        self.accept_button.pack(anchor='w', pady=10)
        self.status = tk.StringVar(value='We check every participant’s access before saving. Insert permission is\nset by the organizer; it cannot be proven by this read-only check.')
        ttk.Label(frame, textvariable=self.status, wraplength=620).pack(anchor='w', pady=5)
        self.finish_button = ttk.Button(frame, text='Check all connections and finish', command=self.finish)
        self.finish_button.pack(anchor='e', pady=8)
        if existing:
            ttk.Label(frame, text='Finishing replaces settings on this Mac. Reopen the app afterward.\nCancel keeps your current settings.', wraplength=620).pack(anchor='w')
        self.window.grab_set()

    def choose_file(self):
        path = filedialog.askopenfilename(parent=self.window, title='Choose group invitation',
            filetypes=[('QOL group invitation', '*.json')])
        if not path:
            return
        try:
            self.load_file(path)
        except (OSError, ValueError) as exc:
            messagebox.showerror('Cannot import invitation', str(exc), parent=self.window)

    def load_file(self, path):
        invitation = read_invitation(path)
        self.invitation = invitation
        names = [row['name'] for row in invitation['participants']]
        self.names['values'] = names
        self.name.set(self.existing.get('user', '') if self.existing.get('user') in names else '')
        self.timezone.set(self.existing.get('timezone', invitation['timezone']))
        self.summary.set(f'{invitation["group_name"]} · {len(names)} participants: ' + ', '.join(names))

    def finish(self):
        if self.busy:
            return
        try:
            if self.invitation is None:
                raise ValueError('Import the group invitation first.')
            if not self.accept.get():
                raise ValueError('Confirm that you understand the group’s shared database access.')
            config = group_config(self.invitation, self.name.get(), self.token.get(), self.timezone.get())
        except ValueError as exc:
            messagebox.showerror('Check setup', str(exc), parent=self.window)
            return
        self.busy = True
        widgets = [self.import_button, self.names, self.token_entry, self.timezone_entry, self.accept_button, self.finish_button]
        for widget in widgets:
            widget.configure(state='disabled')
        self.status.set('Checking access and fields for every participant… Please wait.')
        results = queue.Queue()
        def work():
            try:
                failures = check_connections(config)
                if failures:
                    raise ValueError('Ask the organizer to fix these connections, then retry:\n' +
                                     '\n'.join(f'{name}: {error}' for name, error in failures.items()))
                results.put((True, config))
            except Exception as exc:
                results.put((False, str(exc).replace(config['all_users'][config['user']]['NOTION_TOKEN'], '[token hidden]')))
        threading.Thread(target=work, daemon=True).start()
        def poll():
            if self.closed:
                return
            try:
                ok, value = results.get_nowait()
            except queue.Empty:
                self.poll_id = self.window.after(100, poll)
                return
            self.busy = False
            for widget in widgets:
                widget.configure(state='normal')
            self.names.configure(state='readonly')
            if ok:
                try:
                    save_config(value)
                except (ValueError, OSError) as exc:
                    self.status.set('Could not save settings. Your current account has been kept.')
                    messagebox.showerror('Save failed', str(exc), parent=self.window)
                    return
                self.result = value
                self.token.set('')
                self.closed = True
                self.window.destroy()
            else:
                self.status.set('Setup failed. Your existing settings were kept. Fix the problem and retry.')
                messagebox.showerror('Connection check failed', value, parent=self.window)
        self.poll_id = self.window.after(100, poll)

    def cancel(self):
        if self.poll_id is not None:
            self.window.after_cancel(self.poll_id)
        self.token.set('')
        self.closed = True
        self.window.destroy()


def join_group(parent, existing=None):
    dialog = GroupSetup(parent, existing)
    parent.wait_window(dialog.window)
    return dialog.result


def welcome(parent, individual_setup):
    window = tk.Toplevel(parent)
    window.title('Welcome to QOL Score')
    window.transient(parent)
    window.grab_set()
    choice = []
    frame = ttk.Frame(window, padding=25)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='How will you use QOL Score?', font=('Helvetica', 18, 'bold')).pack(pady=10)
    def choose(value):
        choice.append(value)
        window.destroy()
    ttk.Button(frame, text='Join a group using the organizer’s invitation', command=lambda: choose('group')).pack(fill='x', pady=8)
    ttk.Button(frame, text='Set up my own Notion database', command=lambda: choose('individual')).pack(fill='x', pady=8)
    parent.wait_window(window)
    if not choice:
        return None
    return join_group(parent) if choice[0] == 'group' else individual_setup(parent)


def export_invitation(parent, config):
    name = simpledialog.askstring('Export group invitation', 'Group name:',
                                  initialvalue=config.get('group_name', 'QOL Friends'), parent=parent)
    if name is None:
        return
    try:
        invitation = make_invitation(config, name)
        path = filedialog.asksaveasfilename(parent=parent, title='Save invitation (no token included)',
                                           initialfile='QOL-Friends.qol-group.json', defaultextension='.json')
        if not path:
            return
        from pathlib import Path
        Path(path).write_text(json.dumps(invitation, indent=2) + '\n', encoding='utf-8')
        messagebox.showinfo('Invitation saved', 'This file contains names and database IDs only.\nSend it with the app ZIP. Provide the group token privately.\nThe token must have read and insert access to every listed database.', parent=parent)
    except (ValueError, OSError) as exc:
        messagebox.showerror('Export failed', str(exc), parent=parent)
