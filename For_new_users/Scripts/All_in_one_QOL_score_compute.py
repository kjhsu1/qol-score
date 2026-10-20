import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "For_new_users" / "Scripts"))
from config import load_config
#!/usr/bin/env python3

import json
import sys
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import requests
import QOL_LIB



# !!!!!!!!!!! CHANGE THIS FOR OTHER USERS !!!!!!!!!!!!!!
user = load_config()["user"]

# first_part_of_path = "/Applications/QOL_Score/For_new_users_v2"

base_dir = os.path.dirname(os.path.abspath(__file__))

# dict with all user info
# includes "User Analysis Requests" database
# !!!!!! NOTE: DO NOT PUSH ACTUAL NOTION API TOKENS, BELOW ARE JUST EXAMPLES

all_users = load_config()["all_users"]

DATABASE_ID = all_users[user]["DATABASE_ID"]
NOTION_TOKEN = all_users[user]["NOTION_TOKEN"]
# Analysis Request Database
AR_DATABASE_ID = all_users["User_Analysis_Requests_Database"]["DATABASE_ID"]
AR_NOTION_TOKEN = all_users["User_Analysis_Requests_Database"]["NOTION_TOKEN"]

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# header for Analysis Requests Database
ar_headers = {
    "Authorization": "Bearer " + AR_NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def fetch_latest_streak():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=headers)
    data = response.json()
    results = data.get("results", [])
    
    if not results:
        return None
    
    # Extract the entry with the highest numerical "Name" value
    highest_entry = max(results, key=lambda x: int(x["properties"].get("Name", {}).get("title", [{}])[0].get("plain_text", "0")))
    
    # Get the Streak property from the highest entry
    streak_property = highest_entry.get("properties", {}).get("Streak", {}).get("number", None)
    return streak_property
    
# Function to display QOL score and streak with a background image and custom font
def display_qol_score(score, good_streak, bad_streak):
    root = tk.Tk()
    root.title("QOL Score")

    # Set window size to be larger
    root.geometry("800x600")

    # Set background image (ensure the correct path to your background image)
    username = os.getenv('USER') # get username (ex. /Users/kentahsu)
    background_image_path = f"{base_dir}/../Images/boyyaky.jpg"
    
    if not os.path.exists(background_image_path):
        print(f"Background image not found: {background_image_path}")
        return
    
    background_image = Image.open(background_image_path)
    background_photo = ImageTk.PhotoImage(background_image)
    background_label = tk.Label(root, image=background_photo)
    background_label.place(relwidth=1, relheight=1)

    # Custom font (ensure the font file is in the same directory or provide the full path)
    custom_font = ("Comic Sans MS", 24, "bold")

    # QOL Score Label
    qol_score_label = tk.Label(root, text=f"QOL Score: {score}", font=custom_font, bg="white", fg="black")
    qol_score_label.pack(pady=20)

    # Good Streak Label
    good_streak_label = tk.Label(root, text=f"Good Streak: {good_streak}", font=custom_font, bg="white", fg="black")
    good_streak_label.pack(pady=10)

    # Bad Streak Label
    bad_streak_label = tk.Label(root, text=f"Bad Streak: {bad_streak}", font=custom_font, bg="white", fg="black")
    bad_streak_label.pack(pady=10)

    # Messages based on streaks
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
        
        message_label = tk.Label(root, text=message_text, font=("Comic Sans MS", 24, "bold"), bg="white", fg="red")
        message_label.pack(pady=20)
        
    else:
        message_text = random.choice(good_streak_messages)
        
        message_label = tk.Label(root, text=message_text, font=("Comic Sans MS", 24, "bold"), bg="white", fg="black")
        message_label.pack(pady=20)

    root.mainloop()

def fetch_latest_qol_score():
    """
    Query the Notion database and return the QOL Score
    of the entry with the highest numerical 'Name' value.
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=headers)
    data = response.json()
    results = data.get("results", [])

    if not results:
        return None

    # Find the entry whose Name title is largest when interpreted as an integer
    highest_entry = max(
        results,
        key=lambda x: int(
            x["properties"]
             .get("Name", {})
             .get("title", [{}])[0]
             .get("plain_text", "0")
        )
    )

    # Extract the QOL Score property
    return highest_entry.get("properties", {}) \
                        .get("QOL Score", {}) \
                        .get("number", None)

def main():
    input_json = sys.stdin.read()
    
    if not input_json.strip():
        print("No input data provided.")
        return
    
    data = json.loads(input_json)

    score = fetch_latest_qol_score()

    # Track streaks
    latest_streak = fetch_latest_streak()
    good_streak = 0
    bad_streak = 0
    if latest_streak == 0:
        pass
    elif latest_streak > 0:
        good_streak = latest_streak
    elif latest_streak < 0:
        bad_streak = abs(latest_streak)    
    
    display_qol_score(score, good_streak, bad_streak)

if __name__ == "__main__":
    main()





