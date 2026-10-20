# Portability audit — 2026-10-20 — version 1.3.1

## Significant findings and fixes

1. **Missing bundled timezone database (high):** the build interpreter searches `/opt/anaconda3/share/zoneinfo` and `/opt/anaconda3/share/tzinfo`. The old app did not include fallback `tzdata`. Running the old ZIP with an empty timezone search path reproduced `No time zone found with key America/Los_Angeles`. On a recipient without these developer files, this can prevent account setup, saves and rankings. The bundle now explicitly includes tzdata and frozen launches use that data. Los Angeles, London and Tokyo pass with external timezone paths removed.
2. **Plotting blocked the first window (high):** UI import performed Matplotlib font discovery before creating Tk. Initial discovery took about 14 seconds here; delays vary with the recipient's fonts/environment. Plotting is now loaded on demand for History, with font discovery in its worker. Real first-run onboarding passes without importing Matplotlib or contacting Notion.
3. **Font cache discarded every launch (medium):** PyInstaller's runtime hook replaced MPLCONFIGDIR with a fresh temporary directory before launch.py; the previous setdefault did not override it. The one-folder app now uses a persistent per-user cache. A cold complete GUI test took 16.959 seconds; the same test with the retained cache took 3.144 seconds. These timings include the test's windows, callbacks and plotting, not only startup.
4. **Invalid settings could terminate the app (medium):** malformed connection types passed validation or damaged JSON stopped startup without a recovery workflow. Validate types before client construction; offer to preserve the original in a private timestamped backup and rerun setup. Unique private temporary files also prevent concurrent settings saves colliding. Interrupted replacement preserves the original.
5. **Inadequate startup diagnostics (medium):** a hang before the UI produced no error log. Startup stages and a 30-second Python startup stack trace now go to startup.log; fatal errors still go to last-error.log. Tk callback errors are reported visibly. These diagnostics cannot capture failures before Python starts, such as Gatekeeper rejecting the download.

Removed three tracked compiled QOL_LIB caches; supported launchers continue using shared source. Scoring and Notion payload/streak rules are unchanged.

## Verification

- Host: Apple Silicon arm64, macOS 26.4, CPython 3.11.9. Target: Apple Silicon, macOS 14+.
- **65 unit/regression tests passed**, including all scoring/ranking/onboarding tests and new cold-import, timezone fallback, malformed-settings, backup, interrupted/concurrent-save and offline-control tests.
- Final ZIP extracted to a path with spaces and Japanese characters. Tests use an empty temporary HOME, nonexistent config, no preexisting plotting cache, empty external timezone search path, working directory outside the checkout and system-only PATH. No private config is created; no live Notion requests/writes occur.
- Real first-run welcome: **passed**, no Matplotlib imported. 0.921 seconds from test entry to welcome check; 1.645 seconds for the entire process including bundle startup and automatic close. These timings are observations on this host, not a guarantee for every Mac.
- Packaged input, group import/identity/full roster/cancellation, ranking score/date/streak/partial states, exact scoring, score/analysis windows and plot: **passed**. Bundled timezone and TLS certificate store: **passed**. See smoke-test-results.json.
- Actual Tk offline startup and save preserve typed input and release controls: **passed** with disconnected HTTP mocked. Actual Tk invalid-settings recovery preserves bytes and reopens setup: **passed**.
- All **111** bundled Mach-O files checked: arm64 present, deployment targets no higher than advertised macOS 14, no absolute developer-library dependencies, no missing loader-relative dependencies or broken symlinks. Required Tcl/Tk, timezone, CA and image resources present. Deep strict ad-hoc code signature: **passed**. Build now runs this audit before creating its ZIP; the audit rejects the old 1.3.0 bundle for missing timezone files.
- Read-only live rankings succeeded for Kenta, Kazuma and Eoin with no unavailable participants.
- Private-config exclusion and configured-token scans passed for the bundle, all 723 packaged Python modules, and the source patch.
- No live daily entries were inserted or changed. Existing source regression tests cover mocked Notion save payloads and read errors; this audit does not establish that every real group token has insert permission.

## Release

`dist/QOL-Score-v1.3.1-macOS-arm64.zip`, identical to the stable filename for this build.

SHA-256: `c20c45e097c209f63f297e4b225d39e52e2574822aedf0f1a602019ccbaa5207`

The group invitation format is unchanged; the existing JSON still works. Private account settings/tokens/invitations are not included in the app.

## Remaining platform limits

This is an extensive audit and isolated testing on the development Mac, **not a separate physical Mac, fresh macOS login or VM**. Recipient-side Gatekeeper/quarantine and OS-version behavior still need testing. The app is ad-hoc signed, without Developer ID/notarization, so the recipient may need Privacy & Security → Open Anyway. A macOS 14 VM and another physical M1–M4 Mac remain untested. Intel and macOS 13 or older are outside this release's target. We have not confirmed which defect caused the friend's five-minute failure without their logs.
