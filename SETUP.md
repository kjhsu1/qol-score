# QOL Score: Mac setup and sharing

## Recommended download

Send friends **only** `dist/QOL-Score-macOS-arm64.zip`. Unzip it, drag **QOL Score.app** into Applications, then open it. Python, Conda, Pillow, plotting libraries, images, and fonts are bundled. They do not need to install a developer environment.

This release targets **Apple Silicon (M1 and later), macOS 14 or newer**. It was built and smoke-tested on an Apple Silicon Mac with macOS 26.4. Other physical Macs have not yet been tested. Intel Macs require a separate x86_64 build on an Intel Python installation; do not send them this ARM build.

The local build is ad-hoc signed, not Developer ID signed or notarized. A friend receiving it over the internet may need to open System Settings → Privacy & Security → Open Anyway after attempting to open the app. Only approve a copy received from someone you trust. For distribution without that step, use an Apple Developer ID and notarize the app. Do not disable Gatekeeper globally.

## Recommended onboarding: one master Notion account

The organizer owns **a separate QOL database for each participant** in one Notion workspace. Everyone runs the same app. Each installation saves to its selected person's database and reads the full participant list for rankings. A single database containing everyone's rows is not supported by this setup.

Friends **do not need their own Notion account or integration** when using the organizer's group connection. They need the app ZIP, the group's invitation file, and its token, supplied privately by the organizer.

### Organizer: prepare the group once

1. Create or duplicate an **empty** QOL database for each participant in the master workspace. Use the exact properties in the table below. Keep existing participant databases if their schema already matches. Each participant must have a different database ID and a unique display name.
2. Create a **dedicated internal Notion connection** for this trusted friend group. Enable **Read content** and **Insert content**. The app does not require update/delete capability to submit daily records. Add this connection to every participating database through its Connections menu. Limit its access to the group databases. See [Notion's connection instructions](https://www.notion.com/help/create-integrations-with-the-notion-api).
3. Prepare the invitation. If your current app already lists everyone, choose **Group → Export group invitation…**. Otherwise copy `onboarding/group.example.json`, set your group name/timezone, and add each person's display name and database ID. You can paste an original Notion database URL in place of an ID; the app extracts the database ID and ignores the view ID. Remove all example participants. The invitation contains names and database IDs **only**, never a token.
4. Choose **Group → Join or update group…** on your own Mac. Import the invitation, select your name, paste the dedicated group token, choose your timezone, acknowledge the shared access, and click **Check all connections and finish**. All participant schemas and query access must pass. A failed check lists the affected people and preserves existing settings.
5. Reopen the app and confirm the title shows your name. Open **Rankings** to confirm every participant appears; those without entries show **No score**. The setup check is read-only: it does not prove Insert content permission. Confirm that permission in Notion, and verify a normal save when you make your next real daily entry.
6. Send friends the app ZIP and the same `.qol-group.json` invitation. Provide the dedicated group token through your private communication channel, separately from the public app download. Never send your full `config.json` or put the token in Git, the invitation, or the ZIP.

This is a **trusted-group setup**, not individual authentication. Anyone with the token can read the connected databases, including diary fields, and insert entries into them. Selecting a name routes the app's submissions; it does not prevent someone from using another identity. Use this only with participants who agree to that access. A private score-only competition would need a different backend design.

### Friend: install and join

1. Unzip the app and drag **QOL Score.app** into Applications. Open it. For this release, use an Apple Silicon Mac on macOS 14 or newer.
2. On the welcome screen choose **Join a group using the organizer's invitation**.
3. Click **Import group invitation…**, select the file from the organizer, and choose **your own name** from the list. If your name is missing, ask for an updated invitation; do not choose someone else's name.
4. Paste the group token, set your timezone, and acknowledge the group's shared database access.
5. Click **Check all connections and finish**. Wait for every participant's access check to pass. If there is an error, keep the form open, ask the organizer to fix it, and retry. Cancel leaves existing settings intact, including during a connection check.
6. Check that the app title shows your name, then open **Rankings**. You should see the same participant list as the organizer. Make your first normal daily entry when ready.

The token is masked during setup and saved only in the private settings file on your Mac. No Notion records are created by onboarding. Group invitations do not include optional analysis-service credentials.

### Existing users, new members, and changed tokens

Use **Group → Join or update group…** to join after individual setup, replace a token, or import an updated invitation. Finishing replaces local account settings and asks you to reopen the app. Cancel keeps them. Do not start this while you have an unsaved daily form you want to retain.

When someone joins the group, the organizer adds their database and grants the group connection access, then exports/updates the invitation. **Everyone must re-import the updated invitation** to get the new roster; participant discovery is not automatic. Removing someone from an invitation does not revoke a token they already possess: rotate/revoke the group token in Notion and redistribute it to the remaining participants when access must be removed.

### Optional: individual setup

Choose **Set up my own Notion database** on the welcome screen if you want individual tracking. This asks for your name, own integration token, database ID, and timezone. It configures only your account. For group rankings, subsequently use **Group → Join or update group…**.

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

Group onboarding populates the full `all_users` participant list automatically. Rankings display all configured participants, their latest scores, dates, and current streaks, and explicit **No score** or **Unavailable** rows. If any connection fails, the window is labeled **PARTIAL RANKINGS**; available scores remain visible. Fix the connection and click Rankings again to retry. The Current streak column shows `Good · 4` for four good recorded entries, `Bad · 2` for two bad recorded entries, `No streak` for zero, and `Unknown` when streak data is missing or invalid. Score, date, and streak are all read from the same latest entry.

The existing rule that an off day scores **100** is preserved. Agree on when off days are allowed before competing. Scores are self-reported. Streaks count consecutive recorded entries scoring at least 65 (or below 65), rather than requiring consecutive calendar days.

## Scoring rules (version 1.3.0)

See [SCORING.md](SCORING.md) for every variable and deduction. The app now picks the better of the continuous healthy (60% focus target, 10 points per missed habit) and productive routes (70% baseline, 1.5 points per focus percentage point and 3 points per missed habit, with extra focus offsetting those habit deductions). Ideal bedtime is **11:30 PM**. Wake/social-media penalties, off-day overrides and streak rules retain their existing behavior. These rules apply to new entries; historical Notion records are not recalculated. All competing participants should update to the same version.

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

The offline self-test opens and closes the actual input form, score display, analysis window, ranking window, plot, and group invitation/import flow. It uses dummy configuration and never contacts Notion or submits records. Check that the report contains `"ok": true`.

Before sending broadly, test the ZIP on another Mac with no Python/Conda installed, complete first-run setup using a disposable database, submit one sample day, reopen, confirm the next entry number, test ranking and plotting, and test loss of internet. These recipient-machine tests cannot be replaced by tests on the development Mac.

Do not share a source repository containing old tokens in Git history. Embedded tokens were removed from the feature worktree's files, but historical commits still contain them. Rotate tokens before making that history public. The built app and release ZIP exclude these historical files and private configuration.
