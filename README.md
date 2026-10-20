# QOL_Score

**Mac app release and current setup:** see [SETUP.md](SETUP.md) for the bundled app, Notion configuration, sharing with friends, verification, and platform limits. Both current launchers use the same scoring model.

`QOL_Score` is a Python desktop application that turns daily self-tracking into a structured personal analytics workflow. The project combines a custom scoring model, a local GUI, external API integration, time-series visualization, and lightweight automation patterns to quantify day-to-day quality of life and store the results in Notion.

It is built as an end-to-end personal data product: user input, validation, scoring logic, persistence, trend analysis, ranking, and UI-driven interaction in one cohesive workflow.

## Project Idea

The central idea behind `QOL_Score` is to measure quality of life using a daily blend of behavioral, productivity, and lifestyle inputs rather than relying on a single subjective rating.

Each day, the user logs:

- wake time
- sleep time
- exercise
- whether they went outside
- whether they talked to someone
- minutes spent on social media
- minutes of focused work
- whether the day should be treated as an off day or special day
- a short diary or daily note

Those inputs are transformed into a numerical QOL score out of 100 and saved to Notion, where the data can be used for longitudinal tracking, streak calculation, comparison, and later analysis.

## Why This Project Is Interesting

This project showcases a practical blend of software engineering and product thinking:

- building a full user workflow instead of an isolated algorithm
- translating a subjective concept like "quality of life" into a formal scoring system
- designing a GUI for daily use rather than a developer-only tool
- integrating a third-party API as a persistence layer
- working with time-based data, stateful history, and trend visualization
- structuring a project with separate modules for UI, scoring, extraction, ranking, and automation support

It reflects an engineering style that values experimentation, personalization, iteration, and shipping working tools for real everyday use.

## Technical Skills Demonstrated

This repository demonstrates experience with:

- Python application development
- desktop GUI development with `tkinter`
- REST API integration with the Notion API using `requests`
- modular code organization across multiple scripts
- data validation and user-input handling
- date/time manipulation and timezone-aware formatting
- score computation and heuristic modeling
- data visualization with `matplotlib`
- image handling in desktop apps with `Pillow`
- shell scripting for local app launch and workflow automation
- environment management with Conda

## Core Concepts Used

### 1. Human-centered data modeling

The project models daily life as a set of measurable signals. Instead of asking only "How was your day?", it treats quality of life as something inferable from behavior, routine, and social activity.

### 2. Heuristic scoring system design

The scoring engine in `QOL_LIB.py` applies weighted penalties based on deviations from ideal sleep/wake timing, lack of exercise, lack of outdoor activity, lack of social interaction, excessive social media use, and low productive efficiency. This is a useful example of turning informal wellness intuitions into concrete program logic.

### 3. Stateful historical tracking

The app is not stateless. It reads previous entries to determine:

- the next entry number
- the current streak
- historical score trends
- comparative rankings across users

That makes the project closer to a lightweight analytics product than a one-off form submission tool.

### 4. API-backed desktop software

Rather than storing data only in local files, the application uses Notion as a remote datastore. This demonstrates practical API usage inside a desktop application, including request formatting, pagination, filtering, querying, and writing structured records back to a hosted system.

### 5. Personal analytics and feedback loops

The project closes the loop between logging behavior and receiving feedback by displaying:

- the computed QOL score
- positive or negative streaks
- historical plots
- rankings
- analysis request hooks

This makes the software interactive, interpretive, and behavior-shaping rather than just archival.

## Architecture Overview

The repository is organized around a small set of focused components.

### `For_new_users/Scripts/UI.py`

This is the main application entry point. It builds the Tkinter interface, collects user input, validates fields, computes the score, calculates streaks, submits entries to Notion, and exposes additional actions such as plotting, rankings, and analysis requests.

### `For_new_users/Scripts/QOL_LIB.py`

This file contains the core scoring model. It computes a QOL score from daily input data by combining schedule alignment, behavioral habits, social activity, and focused work efficiency into a single output.

### `For_new_users/Scripts/ranking.py`

This module retrieves the latest score for each configured user and displays a top-three ranking in a themed Tkinter window. It demonstrates cross-user aggregation and presentation logic on top of shared data infrastructure.

### `For_new_users/Scripts/All_in_one_QOL_input_extraction.py`

This script extracts stored data from Notion for a specific entry. It shows how the project separates retrieval and transformation from the main UI workflow.

### `For_new_users/Scripts/All_in_one_QOL_score_compute.py`

This script reads prior data and renders a score/streak display flow. It reflects an earlier or alternate execution path for score display and reinforces the modular decomposition of the application.

### `For_new_users/run_ui.sh`

This launch script configures the shell environment, activates the Conda environment, and starts the GUI application. It is a simple but important example of smoothing the path from codebase to runnable desktop tool.

## Data Flow

At a high level, the application works like this:

1. The user opens the local desktop UI.
2. The app queries Notion to determine the latest entry number and prior streak state.
3. The user enters the day’s inputs.
4. The scoring library computes a QOL score.
5. The app derives the updated streak from score history.
6. The entry is posted to Notion through the API.
7. The user can then inspect trends, rankings, or analysis-related outputs.

This is a compact example of a real application pipeline that includes input, computation, persistence, retrieval, and visualization.

## Toolkit and Libraries

The current implementation uses:

- `Python 3.11+`
- `tkinter` for the desktop UI
- `requests` for HTTP communication with Notion
- `zoneinfo` for timezone handling
- `Pillow` for working with images in the GUI
- `matplotlib` for score plotting and trend visualization
- `bash` for launch automation
- `conda` for reproducible environment setup

## Product and Design Choices

Several choices in this repository are worth highlighting from a product-engineering perspective:

- The UI is designed for repeat daily use, not just one-time execution.
- The scoring model intentionally mixes wellness and productivity signals.
- The app uses Notion as a lightweight backend, which is a pragmatic product decision for a solo or small-scale tool.
- The system includes visual feedback and gamification through streaks and rankings.
- The project supports multiple configured users, not just a single hardcoded workflow.

These decisions show a willingness to think beyond implementation details and toward adoption, motivation, and behavioral feedback.

## Project Structure

```text
QOL_Score/
├── For_new_users/
│   ├── Scripts/
│   │   ├── UI.py
│   │   ├── QOL_LIB.py
│   │   ├── ranking.py
│   │   ├── All_in_one_QOL_input_extraction.py
│   │   └── All_in_one_QOL_score_compute.py
│   ├── Images/
│   ├── Text_Files/
│   ├── environment.yml
│   └── run_ui.sh
├── For_Kenta/
├── Archive/
├── LICENSE
└── README.md
```

## Summary

This project is a strong example of:

- building an end-to-end application instead of just isolated scripts
- combining UI, APIs, data modeling, and visualization in one system
- designing software around a real recurring use case
- turning an abstract concept into a concrete and operational product
- using code as a way to formalize and test a personal framework for measurement and improvement

In short, `QOL_Score` demonstrates product-minded engineering: identifying a problem, designing a model, building an interface, integrating persistence, and creating a feedback system users can return to every day.

## Setup Notes

See [SETUP.md](SETUP.md). The supported source entry point is `For_new_users/run_ui.sh`; `For_Kenta/run_ui.sh` delegates to it. Use Python 3.11 or newer. Account credentials live in the user's private Application Support directory, outside the repository and app bundle.
