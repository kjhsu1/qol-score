# Ajito verification — 2026-10-20

- Build: native arm64, macOS deployment target 11.1; version 2.0.0.
- Physical test host: **Apple M1 Pro, macOS 26.4**. Other M1/M2/M3/M4 hardware and macOS 11.1–15 have not been physically/VM tested. Architecture/deployment inspection and simulated feature absence do not replace that testing.
- **77 unit/regression tests passed.** Existing scoring, validation, Notion-save payload, timezone, onboarding, ranking and streak tests remain. New tests cover source/API scoring parity, selected-database routing, changed-identity rejection, no secret exposure, failed setup preservation, descriptive statistics/sample limits, and loopback API guards.
- Scoring `core.py`, `notion_client.py`, and `group_setup.py` are **byte-identical to main**. Rankings retrieve logic is unchanged; Tk imports were moved into the legacy display function so native API startup excludes Tk.
- **Native WebKit GUI smoke test passed from the final extracted ZIP**: exact healthy 95/productive 97 examples, all three crew scores/dates/good/bad streaks, history, review, demo save, real WebGL-rendered mascot and the More analysis tools. Demo saves cannot call Notion or replace settings.
- **Fresh native setup passed** with a valid empty home directory, unused config, system-only PATH, empty external timezone path and app path containing spaces/Japanese characters. Onboarding is visible, token empty, saving disabled before setup, invitation validation passes, mascot renders. No config/records were created. An earlier harness attempt pointed HOME at a directory that did not exist and stalled Cocoa; rerunning with a valid home and with only an unused QOL_CONFIG passed. Neither is a real new macOS account or VM.
- **Packaged real-account read check passed**: reused existing private settings, all three participants (Kenta, Kazuma, Eoin), latest-entry/history reads and record-based analysis. No write endpoints called. Private tokens/database IDs are not in the reports.
- **Browser failure/compatibility suite passed**: duplicates and invalid inputs blocked; failed saves preserve form/release controls; zero/empty/unavailable ranking rows retained; failed invitation setup preserves identity; actual rendered pixels change while walking and remain still while paused; CSV downloads; widths 1440/1024/800/390 without document overflow; WebGL 1-only/old-dialog/Array.at-absent simulation; disabled-GPU mode still allows scoring.
- Bundle inspection: **55 native binaries** have arm64 code, no deployment target above 11.1, no absolute developer-library paths, no missing loader-relative dependencies or broken symlinks. Timezone/CA/static/3D resources present. Deep strict ad-hoc signature passes. Build starts from an empty app staging folder to avoid retaining deleted files.
- Private-config exclusion and configured-token scans passed for the bundle and **230** packaged Python modules. Tk, Pillow, NumPy and Matplotlib modules are absent from the service archive. Core UI and assets load locally, without CDN requests.
- Native invitation/CSV file panels are implemented using system Open/Save panels. Programmatic browser upload/download paths were tested; completing those macOS panels by hand remains part of recipient acceptance testing.
- No real Notion records were inserted/changed, no historical scores recalculated, no settings/tokens replaced. Read permissions passed; Insert content permissions remain controlled by the existing integration and are not proven by read-only checks.

## Artifact

`dist/QOL-Score-Ajito-v2.0.0-macOS-arm64.zip` — 12,911,520 bytes.

SHA-256: `0de28c1846cb7c4ba5ef6f0053652226760605220f503e42e38110e1aaa1652f`

The same invitation JSON works. Main is unchanged; the work is on `codex/qol-ajito-redesign`, created from main with the earlier portability fixes carried over.

## Remaining recipient checks

On another physical Apple Silicon Mac, download/extract, handle Gatekeeper if prompted, open, import the existing invitation, choose the correct identity, verify rankings, and make a deliberate real daily save when ready. Check the database and reopen. Test file export. The app is not Developer ID signed/notarized and may need Open Anyway. WebGL-disabled environments cannot display the 3D character; core workflows remain usable. No claim is made that every Apple Silicon/OS combination has passed.

## Hat update — 2.0.1

The 3D mascot now has the signature tall twin-pointed green hat, gold ear covers and red B crest. Face geometry is unchanged. Browser interaction/graphics fallback/motion tests and the native WebKit smoke test passed. The architecture/resource/signature build gate passed. No scoring or Notion changes.

SHA-256: `5cd4feb6c845afc22c120d7fbbb6019c76cd28307ae6128ce4edf51ccd92f387`

## Wider hat points — 2.0.2

Spread the green hat points outward and lowered the tips to match the reference silhouette; face geometry is unchanged. Browser interaction, walking/pause, WebGL 1 and graphics fallback tests passed. The rebuilt native WebKit smoke test passed on the M1 Pro host, and the ARM64/resource/signature build gate passed. Scoring and Notion behavior are unchanged.

## Ocean Beach banner and UI cleanup — 2.0.3

Uses the approved less-dramatic Boyacki portrait and banner variation A: dark, forward-slanted Japanese headline with comma and period over a light coastal wash. Noto Sans JP Bold is locally bundled as a small renamed character subset, with its OFL license; font loading passed in both Chromium and native WebKit. Removed the requested decorative labels, score-panel filler and footer; scoring guide stays under More. Validation errors remain visible and clear after correction.

All 77 regression tests passed. Browser tests passed for save review, duplicates, invalid and offline submissions, rankings including partial data, onboarding failure, history, analytics, CSV, walking/pause, widths 1440/1024/800/390, WebGL 1/older dialog fallback and no-GPU core workflow. Packaged native smoke passed on the existing M1 Pro/macOS 26.4 host. ARM64/minimum-OS/resources/signature gate passed for 55 native binaries, including bundled font/license. ZIP assets were compared byte-for-byte against source. Scoring, Notion writes and group setup still match main. This does not add physical testing on other Macs or macOS versions.

ZIP SHA-256: `8864e3d5f0496d7729b583ccb015f5dda7ca9f07984bb85bb477113357fdc224`
