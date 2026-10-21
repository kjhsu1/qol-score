# QOL Score · Boyacky's Ajito

A self-contained native Mac app with a WebKit interface, a 3D Doronbo hideout, a walking Boyacki, and the existing QOL scoring/Notion backend. No hosting, Vercel, browser setup, Python installation, or additional API tokens are needed by recipients.

## Open it

Unzip `dist/QOL-Score-Ajito-v2.0.1-macOS-arm64.zip`, drag **QOL Score Ajito.app** into Applications, and open it. The target is **Apple Silicon, macOS 11.1 or later**. The build is ad-hoc signed, without Developer ID/notarization: a downloaded copy may require System Settings → Privacy & Security → Open Anyway. The original app can remain installed.

Existing installations use the same `~/Library/Application Support/QOL Score/config.json`: same selected person, integration tokens, timezone, database IDs, group roster and optional legacy configuration. There is no migration of Notion records or token rotation. A fresh installation opens Group & settings: import the existing invitation JSON, select your own name, paste the organizer's existing token, and verify connections. Settings changes check every participant and preserve damaged settings in a backup before replacement. Switching identity clears the daily form to avoid carrying another person's diary/inputs across accounts.

## Daily use

Enter the log date, wake/bed times, three habit switches, focus/social-media minutes, optional diary, and off-day flag. Efficiency and projected score update from the shared scoring engine. Use the red skull button in its green housing to review the selected person, date and score, then confirm the save to Notion. Validation, rounding, one-entry-per-date/chronological checks, entry numbering and signed streaks run through the existing client. Errors preserve the form. Timed-out saves should be checked in Notion before another attempt.

Crew rankings use the entire existing roster and show latest score, date and good/bad streak quantity from the same entry. Unavailable/no-entry participants remain visible; incomplete results are labeled partial. Ties follow the existing Python ranking order. History shows daily averages and a rolling seven-entry trend without importing Matplotlib.

## More: analysis and perspective

- **Weekly debrief:** averages of the latest seven unique logged dates and preceding seven; good-day counts and personal best. These are stored scores, without rescoring old records.
- **Focus versus score:** hoverable scatterplot using complete wake/bed/focus inputs. Off days are marked and excluded from the descriptive Pearson correlation. At least five observations and nonzero variance are required to show a coefficient.
- **Habit comparisons:** Yes/No stored-score means and sample counts, excluding off days and missing habit values. Groups with fewer than five samples are explicitly flagged. Focus/timing/scoring-version confounders are explained. No causal or health claims are generated.
- **Weekday patterns:** mean stored scores with sample counts. Small samples remain visible rather than producing confident recommendations.
- **Day lab:** calculate the exact score effect of one change at a time—each missing habit, 30 more focus minutes, 30 fewer social-media minutes, or ideal wake/bed timing. Uses the shared engine; does not apply changes, write records, or invent a new scoring rule.
- **CSV export:** your logged dates, stored scores, focus efficiency and habit/off-day flags, for external analysis. No tokens, database IDs or diary fields are exported.
- **Scoring manual:** the existing rules in full. The obsolete request/receive-analysis workflow is absent from Ajito. No focus timer or unrelated widgets.

Historical scores may span previous versions of the model. Score-input relationships are partly built into the formula and should not be interpreted as evidence of improved wellbeing. The app does not call an LLM or send data to a new service for analysis.

## Appearance and motion

The red/green skull submission control is interactive CSS/SVG. Boyacki is a jointed procedural Three.js model, with a walking cycle, lighting, shadows, and a save reaction. Three.js is bundled, with WebGL 1 compatibility. Motion respects reduced-motion preferences and can be paused. The core app remains usable if graphics initialization fails; the 3D character is unavailable in that case. It cannot render in software configurations that disable WebGL entirely.

Design references inspected during implementation: [Teenage Engineering EP–133](https://teenage.engineering/products/ep-133) for an ivory instrument deck, recessed displays and physical controls; [Poolsuite](https://poolsuite.net/) for a compact desktop-style application. Original layout, controls and assets are included in this repository; no reference-site assets or code were copied. See [asset notes](ajito/ASSETS.md) for artwork provenance and the generation prompt.

## Build and test

Build on Apple Silicon with Apple's Command Line Tools and the existing Python build environment:

```sh
QOL_PYTHON=/path/to/build/python ./ajito/build.sh
```

The script packages the service using PyInstaller, compiles the Cocoa/WebKit window, signs the bundle, checks its native dependencies/arm64 code/minimum OS/resources/signature, and produces the ZIP. All static web and Three.js assets are local. The new app excludes Tk, Pillow, NumPy and Matplotlib. The legacy Tk source launcher remains available as a fallback.

```sh
python -m unittest discover -s tests -v
"dist/QOL Score Ajito.app/Contents/MacOS/QOL Ajito" --smoke-test /tmp/ajito-smoke.json
QOL_CONFIG=/tmp/unused-qol-config.json "dist/QOL Score Ajito.app/Contents/MacOS/QOL Ajito" --setup-check /tmp/ajito-setup.json
"dist/QOL Score Ajito.app/Contents/MacOS/QOL Ajito" --read-check /tmp/ajito-real-reads.json
```

The first mode uses sample data and never writes Notion or private settings. The setup check requires a nonexistent config path and tests first-run onboarding. The read check uses the real local account and calls only read endpoints. Reports must contain `"ok": true`; the process exit code alone does not establish a smoke-test pass.

Browser failure-path tests require Node, Playwright and Chrome **only on the developer machine**:

```sh
QOL_PYTHON=/path/to/python QOL_PLAYWRIGHT=/path/to/playwright node ajito/tests/browser.cjs
```

For a browser preview during development, run `python ajito/service.py --demo` and open the printed local URL. Normal native app launches never expose that URL in the interface. Demo mode uses sample data, cannot connect real accounts, and never calls write endpoints.

The local service binds only `127.0.0.1` with a random port and per-launch secret. Host, origin and token checks protect the API. The window restricts navigation to its local origin; integration tokens stay server-side. Closing the app terminates its service; a parent-process watchdog also stops it after an unexpected wrapper exit. Errors are recorded at `~/Library/Application Support/QOL Score/ajito-error.log`.

## Verified scope

See [test results](ajito/verification/RESULTS.md). Running native ARM64 code and checking deployment targets establishes compatibility requirements, not proof of every hardware/OS combination. Another physical Mac and an older-macOS VM remain necessary recipient tests. This implementation was exercised on an M1 Pro with macOS 26.4; it has not physically run on every M1–M4 configuration.
