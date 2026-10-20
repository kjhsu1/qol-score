import os
from pathlib import Path
import sys
#!/usr/bin/env python3

import requests
import json
import sys

NOTION_TOKEN = os.environ.get('QOL_NOTION_TOKEN', '')
DATABASE_ID = "1144d9b143a9800180f9d91c8934c2cb"  # Data Input for QOL Calculation
DATABASE_2_ID = "0f0518e910de4ca8bf0bf67ddebeefe1"  # Awake Minutes
DATABASE_3_ID = "112ce1b0de0c421cbe3fe424dd729799" # 4.1 Database (Efficiency)

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

    payload = {"page_size": 100}
    response = requests.post(url, json=payload, headers=headers)

    data = response.json()

    results = data["results"]
    return results

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
    for page in pages:
        properties = page["properties"]
        name_property = properties["Name"]["title"]
        if name_property and name_property[0]["plain_text"] == entry_number:
            exercise_property = properties["Exercise?"]["select"]
            went_outside_property = properties["Went Outside?"]["select"]
            talk_to_someone_property = properties["Talk to Someone?"]["select"]["name"]
            min_on_social_media_property = properties["Min. on Social Media"]["number"]
            if exercise_property:
                exercise_values.append(exercise_property["name"])
            if went_outside_property:
                went_outside_values.append(went_outside_property["name"])
            talk_to_someone_values.append(talk_to_someone_property)
            min_on_social_media_values.append(min_on_social_media_property)
    return exercise_values, went_outside_values, talk_to_someone_values, min_on_social_media_values

# Extract values from the Efficiency database
def extract_efficiency_values(pages, entry_number):
    efficiency_values = []
    for page in pages:
        properties = page["properties"]
        name_property = properties["Name"]["title"]
        if name_property and name_property[0]["plain_text"] == entry_number:
            efficiency_property = properties["Efficiency"]["formula"]
            if efficiency_property is not None:
                efficiency_values.append(efficiency_property["string"])
    return efficiency_values

# Print the properties of the first page from Database 3

'''
def print_first_page_properties(pages):
    if pages:
        first_page = pages[0]
        properties = first_page["properties"]
        print(json.dumps(properties, indent=4))
'''

# Get pages from all databases
awake_minutes_pages = get_pages(DATABASE_2_ID)
qol_pages = get_pages(DATABASE_ID)
efficiency_pages = get_pages(DATABASE_3_ID)

# Extract values
wake_times, sleep_times = extract_awake_minutes_values(awake_minutes_pages, entry_number)
exercise_values, went_outside_values, talk_to_someone_values, min_on_social_media_values = extract_qol_values(qol_pages, entry_number)
efficiency_values = extract_efficiency_values(efficiency_pages, entry_number)

# Print the properties of the first page from Database 3
#print_first_page_properties(qol_pages)

all_values = {
    "Wake Times": wake_times,
    "Sleep Times": sleep_times,
    "Exercise Values": exercise_values,
    "Went Outside Values": went_outside_values,
    "Talk to Someone Values": talk_to_someone_values,
    "Min. on Social Media Values": min_on_social_media_values,
    "Efficiency": efficiency_values[0]
}

json_string = json.dumps(all_values, indent=4)
print(json_string)



















