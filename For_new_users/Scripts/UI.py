#!/usr/bin/env python3

import requests
import json
from collections import defaultdict
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, font
from tkinter import scrolledtext
import tkinter.font as tkFont
from datetime import datetime, timedelta
import os
import threading
import random
from PIL import Image, ImageTk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import QOL_LIB # my homemade library 


from core import validate_data
from config import load_config, save_config, config_path
from notion_client import NotionClient
from zoneinfo import ZoneInfo
import queue
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
asset_dir = getattr(sys, "_MEIPASS", os.path.dirname(base_dir))

def get_highest_entry_number():
    client.check_schema()
    return client.highest()


def update_notion_database(data):
    return client.save(data)
def build_default_datetime_strings(now=None):
    if now is None:
        now = datetime.now(ZoneInfo(config['timezone']))

    today = now.strftime("%Y-%m-%d")
    return {
        "wake_time": f"{today}T08:00:00",
        "sleep_time": f"{today}T23:00:00",
        "todays_date": today,
    }


def display_qol_score(data):
    score = data["qol_score"]
    streak = int(data["streak"])
    good_streak = streak if streak > 0 else 0
    bad_streak = abs(streak) if streak < 0 else 0

    score_window = tk.Toplevel(root)
    score_window.title("QOL Score")
    score_window.geometry("800x600")

    background_image_path = f"{asset_dir}/Images/boyyaky.jpg"
    if not os.path.exists(background_image_path):
        messagebox.showerror("Error", f"Background image not found: {background_image_path}")
        score_window.destroy()
        return

    background_image = Image.open(background_image_path)
    background_photo = ImageTk.PhotoImage(background_image)
    score_window.background_photo = background_photo

    background_label = tk.Label(score_window, image=background_photo)
    background_label.place(relwidth=1, relheight=1)

    custom_font = ("Comic Sans MS", 24, "bold")

    qol_score_label = tk.Label(score_window, text=f"QOL Score: {score}", font=custom_font, bg="white", fg="black")
    qol_score_label.pack(pady=20)

    good_streak_label = tk.Label(score_window, text=f"Good Streak: {good_streak}", font=custom_font, bg="white", fg="black")
    good_streak_label.pack(pady=10)

    bad_streak_label = tk.Label(score_window, text=f"Bad Streak: {bad_streak}", font=custom_font, bg="white", fg="black")
    bad_streak_label.pack(pady=10)

    good_streak_messages = [
        "You just a chill guy like that. Keep at it my friend.",
        "君の未来は明るい",
        "そなたは美しい"
    ]

    bad_streak_messages = [
        "ggs my friend, on to the next",
        "my guy, tomorrow's gonna be a better day.",
        "オワコンやんけ"
    ]

    if bad_streak > good_streak:
        message_text = random.choice(bad_streak_messages)
        message_label = tk.Label(score_window, text=message_text, font=custom_font, bg="white", fg="red")
    else:
        message_text = random.choice(good_streak_messages)
        message_label = tk.Label(score_window, text=message_text, font=custom_font, bg="white", fg="black")

    message_label.pack(pady=20)

def resize_image(image_path, width, height):
    image = Image.open(image_path)
    resized_image = image.resize((width, height), Image.LANCZOS)  # Use Image.LANCZOS instead of Image.ANTIALIAS
    return ImageTk.PhotoImage(resized_image)

def fetch_qol_entries():
    entries = []
    for page in client.query(sorts=[{'property': 'Date', 'direction': 'ascending'}]):
        props = page.get('properties', {})
        date = (props.get('Date', {}).get('date') or {}).get('start')
        score = props.get('QOL Score', {}).get('number')
        if date and score is not None:
            entries.append((date, float(score)))
    return entries

def plot_qol_score(entries):
    if not entries:
        messagebox.showwarning("No Data", "No QOL data available to plot.")
        return

    scores_by_day = defaultdict(list)
    for date, score in entries:
        day = datetime.fromisoformat(date).date()
        scores_by_day[day].append(score)

    plot_dates = sorted(scores_by_day)
    daily_scores = [
        sum(scores_by_day[day]) / len(scores_by_day[day])
        for day in plot_dates
    ]

    rolling_window = min(7, len(daily_scores))
    trend_scores = []
    for index in range(len(daily_scores)):
        start_index = max(0, index - rolling_window + 1)
        window_scores = daily_scores[start_index:index + 1]
        trend_scores.append(sum(window_scores) / len(window_scores))

    figure, axis = plt.subplots(figsize=(12, 6))
    axis.scatter(plot_dates, daily_scores, color='#3B82F6', s=28, alpha=0.75, label='Daily average')
    axis.plot(plot_dates, trend_scores, color='#1D4ED8', linewidth=2.5, label=f'{rolling_window} logged-day trend')
    axis.set_xlabel('Date')
    axis.set_ylabel('QOL Score')
    axis.set_title('QOL Score Over Time')
    axis.set_ylim(0, 100)
    axis.grid(True, linestyle='--', alpha=0.35)
    axis.legend(frameon=False)

    date_locator = mdates.AutoDateLocator(minticks=6, maxticks=12)
    axis.xaxis.set_major_locator(date_locator)
    axis.xaxis.set_major_formatter(mdates.ConciseDateFormatter(date_locator))
    figure.autofmt_xdate()
    figure.tight_layout()
    plt.show()

# return "Streak" prop. value in database given entry number
def fetch_streak_by_name(entry_name):
    return client.streak(entry_name)

# gets all user input data into a single dictionary
# also adds QOL score and streak value as well
# returns that dictionary
def get_values_from_user():
    data = validate_data({
        'wake_time': wake_time_entry.get().strip(),
        'sleep_time': sleep_time_entry.get().strip(),
        'exercise': exercise_var.get(), 'outside': outside_var.get(), 'talk': talk_var.get(),
        'social_media': social_media_entry.get().strip(),
        'todays_date': todays_date_entry.get().strip(),
        'time_focused': time_focused_entry.get().strip(),
        'offday_special_day': offday_special_day_var.get(), 'diary': diary_entry.get().strip()})
    data['qol_score'] = round(QOL_LIB.calculate_qol_score(data), 1)
    return data


def update_and_display_everything():
    try:
        data = get_values_from_user()
    except ValueError as exc:
        messagebox.showerror('Check your entry', str(exc), parent=root)
        return
    def saved(result):
        entry_number_entry.config(state='normal')
        entry_number_entry.delete(0, tk.END)
        entry_number_entry.insert(0, str(int(result['entry_number']) + 1))
        entry_number_entry.config(state='readonly')
        display_qol_score(result)
    run_async(lambda: update_notion_database(data), saved)


def run_ranking_as_subprocess():
    import ranking
    run_async(lambda: ranking.retrieve_all_users_QOL(all_users),
              lambda scores: ranking.display_it(ranking.get_top_three(scores), parent=root))

# update the analysis request database
def update_analysis_request_database():
    connection = all_users.get('User_Analysis_Requests_Database')
    if not connection:
        raise ValueError('Analysis requests have not been configured for this account.')
    ar_client = NotionClient(connection, config['timezone'])
    ar_client.resolve()
    ar_client.request('POST', 'pages', json={
        'parent': {'data_source_id': ar_client.source_id},
        'properties': {'Username': {'title': [{'text': {'content': user}}]},
                       'Request Date': {'date': {'start': datetime.now(ZoneInfo(config['timezone'])).date().isoformat()}}}})
    return True

# analysis request = AR
def ar():
    run_async(update_analysis_request_database,
              lambda result: messagebox.showinfo('Success', 'Analysis request sent successfully!', parent=root))

# tkinter display the analysis results
def display_analysis_results(root, analysis_property):
    # Create a new top-level window instead of Tk()
    analysis_window = tk.Toplevel(root)
    analysis_window.title("Analysis Results")
    analysis_window.geometry("900x700")  # Keep window size large

    # Load and set the background image
    background_image = Image.open(f"{asset_dir}/Images/medalist.jpeg")
    background_photo = ImageTk.PhotoImage(background_image)

    # Keep a reference in root to avoid garbage collection
    analysis_window.background_photo = background_photo  

    background_label = tk.Label(analysis_window, image=background_photo)
    background_label.place(relwidth=1, relheight=1)

    # Load retro font
    font_path = f"{asset_dir}/Text_Files/Press_Start_2P/PressStart2P-Regular.ttf"
    
    # Adjusted fonts for better proportions
    title_font = tkFont.Font(family="Press Start 2P", size=18)  # Title is big but not overwhelming
    text_font = tkFont.Font(family="Press Start 2P", size=12)   # Text is readable without stretching

    # Title label (Bigger & Centered)
    title_label = tk.Label(analysis_window, text="Analysis Results", font=title_font, bg="white", fg="black")
    title_label.place(relx=0.5, rely=0.07, anchor="center")

    # Scrollable text box (Shrunk width further)
    text_area = scrolledtext.ScrolledText(
        analysis_window, wrap=tk.WORD, font=text_font, 
        bg="black", fg="lime", width=50, height=30  # Further reduced width + balanced height
    )
    text_area.insert(tk.INSERT, analysis_property)  # Insert analysis report
    text_area.config(state=tk.DISABLED)  # Make it read-only
    text_area.place(relx=0.5, rely=0.55, anchor="center")  # Keep it centered

# check for new Analysis
# THIS FUNCTION IS WORK IN PROGRESS
def check_for_analysis():
    def fetch():
        page = client.latest()
        if not page:
            return 'No entries yet.'
        text = page.get('properties', {}).get('Analysis', {}).get('rich_text', [])
        return ''.join(part.get('plain_text', part.get('text', {}).get('content', '')) for part in text) or 'No analysis is available yet.'
    run_async(fetch, lambda text: display_analysis_results(root, text))

def first_run(parent):
    from tkinter import simpledialog
    values = {}
    for key, prompt, default in [
        ('user', 'Your display name:', ''),
        ('token', 'Your Notion integration token (stored privately on this Mac):', ''),
        ('database', 'Your Notion database ID (32 characters; see setup guide):', ''),
        ('timezone', 'Your timezone:', 'America/Los_Angeles')]:
        value = simpledialog.askstring('Set up QOL Score', prompt, initialvalue=default,
                                       show='*' if key == 'token' else '', parent=parent)
        if value is None:
            return None
        values[key] = value.strip()
    result = {'user': values['user'], 'timezone': values['timezone'],
              'all_users': {values['user']: {'NOTION_TOKEN': values['token'], 'DATABASE_ID': values['database']}}}
    try:
        save_config(result)
    except (ValueError, OSError) as exc:
        messagebox.showerror('Setup failed', str(exc), parent=parent)
        return None
    return result


def run_async(work, success):
    # Workers only touch Python data. Every Tk operation runs in this polling callback.
    if any(str(button['state']) == 'disabled' for button in controls):
        return
    for button in controls:
        button.config(state='disabled')
    status_var.set('Working…')
    results = queue.Queue()
    def worker():
        try:
            results.put((True, work()))
        except Exception as exc:
            results.put((False, str(exc)))
    threading.Thread(target=worker, daemon=True).start()
    def poll():
        try:
            ok, result = results.get_nowait()
        except queue.Empty:
            root.after(100, poll)
            return
        for button in controls:
            button.config(state='normal')
        status_var.set(f'{user} · {config["timezone"]}')
        if ok:
            try:
                success(result)
            except Exception as exc:
                messagebox.showerror('Display error', str(exc), parent=root)
        else:
            status_var.set('Connection or input error. You can retry; your form has been kept.')
            messagebox.showerror('QOL Score', result, parent=root)
    root.after(100, poll)


def main(on_ready=None):
    global root, config, user, all_users, client, controls, status_var, entry_number_entry, wake_time_entry, sleep_time_entry, exercise_var, outside_var, talk_var, social_media_entry, todays_date_entry, time_focused_entry, offday_special_day_var, diary_entry
    # MAIN TKINTER THREAD
    root = tk.Tk()
    root.title("Daily QOL Data Input")
    try:
        config = load_config()
    except ValueError as exc:
        messagebox.showerror('Configuration error', str(exc), parent=root)
        root.destroy()
        return
    if config is None:
        config = first_run(root)
        if config is None:
            root.destroy()
            return
    config.setdefault('timezone', 'America/Los_Angeles')
    user = config['user']
    all_users = config['all_users']
    client = NotionClient(all_users[user], config['timezone'])
    root.title(f'QOL Score — {user}')

    # Set the initial window size (width x height)
    root.geometry(f"{min(1100, root.winfo_screenwidth()-80)}x{min(900, root.winfo_screenheight()-100)}")  # Adjust the size as needed

    # Make the window resizable
    root.resizable(True, True)

    # Load pixel art background
    background_image = tk.PhotoImage(file=f"{asset_dir}/Images/pixel_smile_background.png")  # Replace with your image path
    background_label = tk.Label(root, image=background_image)
    background_label.place(relwidth=1, relheight=1)

    # Set retro font
    font_path = f"{asset_dir}/Text_Files/Press_Start_2P/PressStart2P-Regular.ttf"  # Path to your .ttf file
    retro_font = tkFont.Font(family="Press Start 2P", size=12)  # Load the font using Tkinter
    highest_entry_number = 0
    default_datetimes = build_default_datetime_strings()

    # Configure grid to be resizable
    for i in range(14):
        root.grid_rowconfigure(i, weight=1)
    for i in range(2):
        root.grid_columnconfigure(i, weight=1)

    tk.Label(root, text="Entry Number (automatic)", font=retro_font, bg="black", fg="white").grid(row=0, column=0, sticky="nsew")
    entry_number_entry = tk.Entry(root, font=retro_font, bg="black", fg="white")
    entry_number_entry.insert(0, str(highest_entry_number + 1))
    entry_number_entry.config(state='readonly')
    entry_number_entry.grid(row=0, column=1, sticky="nsew")

    tk.Label(root, text="Wake Time (YYYY-MM-DDTHH:MM:SS)", font=retro_font, bg="black", fg="white").grid(row=1, column=0, sticky="nsew")
    wake_time_entry = tk.Entry(root, font=retro_font, bg="black", fg="white")
    wake_time_entry.insert(0, default_datetimes["wake_time"])
    wake_time_entry.grid(row=1, column=1, sticky="nsew")

    tk.Label(root, text="Sleep Time (YYYY-MM-DDTHH:MM:SS)", font=retro_font, bg="black", fg="white").grid(row=2, column=0, sticky="nsew")
    sleep_time_entry = tk.Entry(root, font=retro_font, bg="black", fg="white")
    sleep_time_entry.insert(0, default_datetimes["sleep_time"])
    sleep_time_entry.grid(row=2, column=1, sticky="nsew")

    exercise_var = tk.StringVar(value="No")
    tk.Label(root, text="Exercise?", font=retro_font, bg="black", fg="white").grid(row=3, column=0, sticky="nsew")
    exercise_menu = tk.OptionMenu(root, exercise_var, "Yes", "No")
    exercise_menu.config(font=retro_font, bg="black", fg="white")
    exercise_menu.grid(row=3, column=1, sticky="nsew")

    outside_var = tk.StringVar(value="No")
    tk.Label(root, text="Went Outside?", font=retro_font, bg="black", fg="white").grid(row=4, column=0, sticky="nsew")
    outside_menu = tk.OptionMenu(root, outside_var, "Yes", "No")
    outside_menu.config(font=retro_font, bg="black", fg="white")
    outside_menu.grid(row=4, column=1, sticky="nsew")

    talk_var = tk.StringVar(value="No")
    tk.Label(root, text="Talk to Someone?", font=retro_font, bg="black", fg="white").grid(row=5, column=0, sticky="nsew")
    talk_menu = tk.OptionMenu(root, talk_var, "Yes", "No")
    talk_menu.config(font=retro_font, bg="black", fg="white")
    talk_menu.grid(row=5, column=1, sticky="nsew")

    tk.Label(root, text="Min. on Social Media", font=retro_font, bg="black", fg="white").grid(row=6, column=0, sticky="nsew")
    social_media_entry = tk.Entry(root, font=retro_font, bg="black", fg="white")
    social_media_entry.grid(row=6, column=1, sticky="nsew")

    tk.Label(root, text="Today's Date (YYYY-MM-DD)", font=retro_font, bg="black", fg="white").grid(row=7, column=0, sticky="nsew")
    todays_date_entry = tk.Entry(root, font=retro_font, bg="black", fg="white")
    todays_date_entry.insert(0, default_datetimes["todays_date"])
    todays_date_entry.grid(row=7, column=1, sticky="nsew")

    tk.Label(root, text="Time Focused (minutes)", font=retro_font, bg="black", fg="white").grid(row=8, column=0, sticky="nsew")
    time_focused_entry = tk.Entry(root, font=retro_font, bg="black", fg="white")
    time_focused_entry.grid(row=8, column=1, sticky="nsew")

    offday_special_day_var = tk.StringVar(value="No")
    tk.Label(root, text="Offday/Special Day?", font=retro_font, bg="black", fg="white").grid(row=9, column=0, sticky="nsew")
    offday_menu = tk.OptionMenu(root, offday_special_day_var, "Yes", "No")
    offday_menu.config(font=retro_font, bg="black", fg="white")
    offday_menu.grid(row=9, column=1, sticky="nsew")

    # Diary
    tk.Label(root, text="Diary (Separate Events by ',')", font=retro_font, bg="black", fg="white").grid(row=10, column=0, sticky="nsew")
    diary_entry = tk.Entry(root, font=retro_font, bg="black", fg="white")
    diary_entry.grid(row=10, column=1, sticky="nsew")

    # Resize the submit button image
    submit_button_image = resize_image(f"{asset_dir}/Images/boyyaky_button.png", 65, 65)
    submit_button = tk.Button(root, image=submit_button_image, text="Save day", compound="left", command=update_and_display_everything, borderwidth=0)
    submit_button.grid(row=11, column=0, columnspan=2, sticky="nsew")

    # Configure plot button with ttk
    style = ttk.Style()
    style.configure("TButton", font=retro_font, background="yellow", foreground="blue")

    # Keep references to the images to prevent garbage collection
    plot_button_image = resize_image(f"{asset_dir}/Images/kabu_chart_man_happy.jpg", 100, 65)
    ranking_button_image = resize_image(f"{asset_dir}/Images/jyaian.jpg", 65, 65)
    request_button_image = resize_image(f"{asset_dir}/Images/yugioh.jpg", 100, 65)
    check_analysis_image = resize_image(f"{asset_dir}/Images/mail.jpg", 65, 65)

    plot_button = tk.Button(root, image=plot_button_image, text="History", compound="left", command=lambda: run_async(fetch_qol_entries, plot_qol_score), borderwidth=0)
    plot_button.grid(row=12, column=0, sticky="nsew")

    ranking_button = tk.Button(root, image=ranking_button_image, text="Rankings", compound="left", command=run_ranking_as_subprocess, borderwidth=0)
    ranking_button.grid(row=13, column=0, sticky="nsew")

    # request analysis button
    request_analysis_button = tk.Button(root, image=request_button_image, text="Request analysis", compound="left", command=ar, borderwidth=0)
    request_analysis_button.grid(row=12, column=1, sticky="nsew")

    # check for analysis button
    check_analysis = tk.Button(root, image=check_analysis_image, text="Check analysis", compound="left", command=check_for_analysis, borderwidth=0)
    check_analysis.grid(row=13, column=1, sticky="nsew")

    controls = [submit_button, plot_button, ranking_button, request_analysis_button, check_analysis]
    status_var = tk.StringVar(value='Connecting to Notion…')
    tk.Label(root, textvariable=status_var, bg='black', fg='white').grid(row=14, column=0, columnspan=2, sticky='ew')
    def connected(highest):
        entry_number_entry.config(state='normal')
        entry_number_entry.delete(0, tk.END)
        entry_number_entry.insert(0, str(highest + 1))
        entry_number_entry.config(state='readonly')
    root.protocol('WM_DELETE_WINDOW', root.destroy)
    run_async(get_highest_entry_number, connected)
    root.update_idletasks()

    if on_ready is not None:
        root.after(1500, lambda: on_ready(root))
    root.mainloop()


if __name__ == '__main__':
    main()
