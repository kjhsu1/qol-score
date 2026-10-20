# Verification — 2026-10-20 — version 1.3.0

- Host: Apple Silicon arm64, macOS 26.4, CPython 3.11.9.
- Regression suite: **58 tests passed**. Includes the approved healthy/productive examples, 11:30 PM ideal bedtime and form default, midnight handling, timing caps, social-media thresholds, off-day override, and both legacy/shared launchers.
- Tested every whole-minute focus input across a 15-hour waking day for all eight habit combinations: more focus never lowers the score and no increment exceeds the approved continuous deduction rate. Completing a habit never lowers the score.
- Mocked save integration checks the newly calculated score in the actual Notion request payload and the resulting streak. No live records were created or edited during this change; historical scores/streaks were not recalculated.
- Rebuilt ZIP extracted into a path containing spaces: **offline packaged GUI test passed**. Verified exact healthy/productive scores and 11:30 PM bedtime, group setup/cancellation, streak cells, score/analysis windows and plotting. See smoke-test-results.json.
- `codesign --verify --deep --strict`: **passed** (ad-hoc signature; no Developer ID/notarization). Bundle version: **1.3.0**.
- Bundled module scan against configured private tokens and private-config exclusion: **passed**.
- `git diff --check` and Python source syntax: **passed**.

## Scoring

Healthy deduction: `max(0, 60 - focus_percentage) + 10 * missed_habits`.

Productive deduction: `max(0, 1.5 * (70 - focus_percentage) + 3 * missed_habits)`.

Choose the smaller deduction from 100, then apply the existing wake/social-media penalties and bedtime penalty anchored to **23:30** on the waking day. Off-day override, validation, rounding and streak rules retain their existing behavior. See SCORING.md for the full guide.

## Release

`dist/QOL-Score-v1.3.0-macOS-arm64.zip` (identical contents to the stable filename `dist/QOL-Score-macOS-arm64.zip`).

SHA-256: `bb17aeb37545be0a1ca966e5841c6dde61a9050a040bb81d36f9d2eb79e26486`

Target: Apple Silicon, macOS 14+. Another physical Mac and Intel hardware remain untested. The unit save tests use mocked HTTP; the existing live database access/submission behavior was checked separately in earlier versions. Private account settings and group invitations are not bundled. Older entries remain scored under their original model, so all competing participants should update together for new entries.
