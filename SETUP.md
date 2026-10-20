# QOL Score: Mac setup and sharing

## Recommended download

Send friends **only** `dist/QOL-Score-macOS-arm64.zip`. Unzip it, drag **QOL Score.app** into Applications, then open it. Python, Conda, Pillow, plotting libraries, images, and fonts are bundled. They do not need to install a developer environment.

This release targets **Apple Silicon (M1 and later), macOS 14 or newer**. It was built and smoke-tested on an Apple Silicon Mac with macOS 26.4. Other physical Macs have not yet been tested. Intel Macs require a separate x86_64 build on an Intel Python installation; do not send them this ARM build.

The local build is ad-hoc signed, not Developer ID signed or notarized. A friend receiving it over the internet may need to open System Settings → Privacy & Security → Open Anyway after attempting to open the app. Only approve a copy received from someone you trust. For distribution without that step, use an Apple Developer ID and notarize the app. Do not disable Gatekeeper globally.

## First launch: connect Notion

Notion remains the backend, so each friend needs a Notion account and an integration. On the first launch the app asks for a display name, integration token, database ID, and IANA timezone (for example `America/Los_Angeles` or `Europe/London`).

1. Create an empty Notion database with exactly one data source. You can duplicate an empty QOL database template; remove sample entries before using it. Do not give friends a database containing someone else's diary.
2. Create an internal Notion connection at [Notion integrations](https://www.notion.so/profile/integrations). Enable reading and inserting content. In the database's Connections menu, grant that connection access.
3. Copy its integration token and the database ID into the setup prompts. The database ID is the 32-character ID in the database URL, before any `?v=` view identifier. Paste the ID, not the entire URL. Use the original database's ID, not a linked view's ID.
4. The app checks the schema on startup. If a field is missing or has the wrong type, it tells you which one to fix. Reopen the app after correcting account settings.

The required database properties are case-sensitive:

| Property | Notion type |
| --- | --- |
| Name | Title |
| Wake Time | Date |
| Sleep Time | Date |
| Exercise? | Select (`Yes`, `No`) |
| Went Outside? | Select (`Yes`, `No`) |
| Talk to Someone? | Select (`Yes`, `No`) |
| Min. on Social Media | Number |
| Date | Date |
| Time Focused | Number |
| Offday/Special Day? | Select (`Yes`, `No`) |
| QOL Score | Number |
| Streak | Number |
| Diary | Text |
| Analysis | Text (optional, for externally supplied analysis) |

Account settings are stored privately at `~/Library/Application Support/QOL Score/config.json`, outside the app, with owner-only file permissions. You can edit this file to correct a token, database ID, or timezone. To rerun setup, rename the file and reopen the app. Keep the file private: it contains access tokens. `QOL_CONFIG` can select another configuration file for testing or separate accounts.

The existing local account was migrated into this configuration during development. No existing Notion entries were modified.

## Competing with friends

Everyone should use this same app version. The older Kenta and newer user models previously awarded different scores for identical inputs; both launchers now use the shared model.

Rankings show each configured person's latest numbered entry, including zero scores. Entries with equal scores sort by display name. Dates can differ: this is a latest-entry leaderboard, not a same-date competition. Agree on a daily submission deadline if comparing days.

Add participating accounts under `all_users` in your private config to enable their rankings. For example (dummy values):

```json
{
  "user": "Alice",
  "timezone": "America/Los_Angeles",
  "all_users": {
    "Alice": {"NOTION_TOKEN": "your-own-token", "DATABASE_ID": "your-database-id"},
    "Bob": {"NOTION_TOKEN": "authorized-read-token", "DATABASE_ID": "bobs-database-id"}
  }
}
```

Each ranking connection must have permission to read that participant's database. Notion database access can expose diary fields too; only add participants who agree to that access. Do not distribute your private config or someone else's write token. A public score-only leaderboard with private diaries would require a separate shared score store; this version retains the existing per-user Notion design.

The existing rule that an off day scores **100** is preserved. Agree on when off days are allowed before competing. Scores are self-reported. Streaks count consecutive recorded entries scoring at least 65 (or below 65), rather than requiring consecutive calendar days.

## Daily use and safeguards

- Enter wake time on the day being logged, and bedtime later that day or early the next day. If bedtime is entered after midnight with the same date as waking, the app moves it to the next day before calculating and saving.
- Minutes must be whole, nonnegative values and cannot exceed the time awake. Invalid dates, equal wake/sleep times, and periods of 24 hours or longer are rejected.
- Entries are numbered automatically. One entry per date is allowed; edits belong in Notion. Submit dates in order so recorded streaks remain consistent.
- While a request runs, action buttons are disabled and the form remains responsive. Network errors preserve the form. If saving times out, inspect Notion before trying again: a server can accept a save even if its response never reaches the app.
- Duplicate checks prevent ordinary repeat submissions, but Notion does not provide an atomic uniqueness constraint. Avoid submitting the same account simultaneously from two devices.
- Analysis requests need an optional `User_Analysis_Requests_Database` connection with `Username` (Title) and `Request Date` (Date). Analysis is not generated by the app itself. Missing analysis shows a message instead of crashing.
- App startup failures are logged to `~/Library/Application Support/QOL Score/last-error.log`.

## Run from source

Use Python 3.11 or newer with Tk support. The [python.org macOS installer](https://www.python.org/downloads/macos/) includes Tk. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
./For_new_users/run_ui.sh
```

`For_Kenta/run_ui.sh` delegates to the same app. Neither launcher requires a fixed checkout folder. `QOL_PYTHON=/path/to/python` overrides interpreter selection. Historical `All_in_one_*` scripts and Archive are not supported app entry points.

## Build and verify

Build on the architecture you intend to distribute. The checked-in lock file records the exact dependencies used for the Apple Silicon build:

```sh
.venv/bin/python -m pip install -r packaging/requirements-macos-arm64.lock
QOL_PYTHON="$PWD/.venv/bin/python" ./packaging/build_macos.sh
.venv/bin/python -m unittest discover -s tests -v
"dist/QOL Score.app/Contents/MacOS/QOL Score" --self-test /tmp/qol-self-test.json
```

The offline self-test opens and closes the actual input form, score display, analysis window, ranking window, and plot. It uses dummy configuration and never contacts Notion or submits records. Check that the report contains `"ok": true`.

Before sending broadly, test the ZIP on another Mac with no Python/Conda installed, complete first-run setup using a disposable database, submit one sample day, reopen, confirm the next entry number, test ranking and plotting, and test loss of internet. These recipient-machine tests cannot be replaced by tests on the development Mac.

Do not share a source repository containing old tokens in Git history. Embedded tokens were removed from the feature worktree's files, but historical commits and the untouched original checkout still contain them. Rotate tokens before making that history public. The built app and release ZIP exclude these historical files and private configuration.
