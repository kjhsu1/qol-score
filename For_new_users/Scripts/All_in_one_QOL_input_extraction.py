import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "For_new_users" / "Scripts"))
from config import load_config
#!/usr/bin/env python3

import requests
import json
import sys
import os

# !!!!!!!!!!!! CHANGE THIS FOR OTHER USERS !!!!!!!!!!!
user = load_config()["user"]


# dict with all user info
# includes "User Analysis Requests" database
# !!!!!! NOTE: DO NOT PUSH ACTUAL NOTION API TOKENS, BELOW ARE JUST EXAMPLES

all_users = load_config()["all_users"]

DATABASE_ID = all_users[user]["DATABASE_ID"]
NOTION_TOKEN = all_users[user]["NOTION_TOKEN"]

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# entry number of interest
entry_number = str(sys.argv[1])
# entry_number = "145"

# Query the database
def get_pages(database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    all_results = []
    has_more = True
    start_cursor = None
    while has_more:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results = data.get("results", [])
        all_results.extend(results)
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    return all_results

# Extract values from the Awake Minutes database
def extract_awake_minutes_values(pages, entry_number):
    wake_times = []
    sleep_times = []
    for page in pages:
        properties = page["properties"]
        name_property = properties["Name"]["title"]
        if name_property and name_property[0]["plain_text"] == entry_number:
            wake_time_property = properties["Wake Time"]["date"]
            sleep_time_property = properties["Sleep Time"]["date"]
            if wake_time_property:
                wake_time = wake_time_property["start"]
                wake_times.append(wake_time)
            if sleep_time_property:
                sleep_time = sleep_time_property["start"]
                sleep_times.append(sleep_time)
    return wake_times, sleep_times

# Extract values from the Data Input for QOL Calculation database
def extract_qol_values(pages, entry_number):
    exercise_values = []
    went_outside_values = []
    talk_to_someone_values = []
    min_on_social_media_values = []
    offday_special_day_values = []
    for page in pages:
        properties = page["properties"]
        name_property = properties["Name"]["title"]
        if name_property and name_property[0]["plain_text"] == entry_number:
            exercise_property = properties["Exercise?"]["select"]
            went_outside_property = properties["Went Outside?"]["select"]
            talk_to_someone_property = properties["Talk to Someone?"]["select"]["name"]
            min_on_social_media_property = properties["Min. on Social Media"]["number"]
            offday_special_day_property = properties["Offday/Special Day?"]["select"]["name"]
            if exercise_property:
                exercise_values.append(exercise_property["name"])
            if went_outside_property:
                went_outside_values.append(went_outside_property["name"])
            talk_to_someone_values.append(talk_to_someone_property)
            min_on_social_media_values.append(min_on_social_media_property)
            offday_special_day_values.append(offday_special_day_property)
    return exercise_values, went_outside_values, talk_to_someone_values, min_on_social_media_values, offday_special_day_values

# Extract values from the Efficiency database
def extract_efficiency_values(pages, entry_number):
    efficiency_values = []
    for page in pages:
        properties = page["properties"]
        name_property = properties["Name"]["title"]
        if name_property and name_property[0]["plain_text"] == entry_number:
            efficiency_property = properties["Efficiency"]["formula"]
            if efficiency_property is not None:
                efficiency_values.append(efficiency_property["number"])
    return efficiency_values

# Print the properties of the first page from Database 3
# use this function to see structure of JSON
def print_first_page_properties(pages):
    if pages:
        first_page = pages[0]
        properties = first_page["properties"]
        print(json.dumps(properties, indent=4))


# Get pages from all in one database
all_in_one_pages = get_pages(DATABASE_ID)

# print_first_page_properties(all_in_one_pages) # testing

# Extract values
wake_times, sleep_times = extract_awake_minutes_values(all_in_one_pages, entry_number)
exercise_values, went_outside_values, talk_to_someone_values, min_on_social_media_values, offday_special_day_values = extract_qol_values(all_in_one_pages, entry_number)
efficiency_values = extract_efficiency_values(all_in_one_pages, entry_number)

# Print the properties of the first page from Database 3
#print_first_page_properties(qol_pages)

all_values = {
    "Wake Times": wake_times,
    "Sleep Times": sleep_times,
    "Exercise Values": exercise_values,
    "Went Outside Values": went_outside_values,
    "Talk to Someone Values": talk_to_someone_values,
    "Min. on Social Media Values": min_on_social_media_values,
    "Efficiency": efficiency_values,
    "Offday/Special Day?": offday_special_day_values
}

json_string = json.dumps(all_values, indent=4)
print(json_string)


















