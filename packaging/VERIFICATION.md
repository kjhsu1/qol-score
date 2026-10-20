# Verification — 2026-10-19

- Host: Apple Silicon arm64, macOS 26.4, Python 3.11.9.
- Final regression suite: **27 tests passed** (`python -m unittest discover -s tests -q`).
- Bundled executable offline self-test: **passed**. Exercised form input/scoring, score window, analysis window, ranking window, and TkAgg plotting.
- Recipient simulation: **passed** after extracting the release ZIP into a directory containing spaces and launching with a fresh HOME and configuration path.
- Code signature: `codesign --verify --deep --strict` **passed** (ad-hoc signature; no Developer ID or notarization).
- Source syntax and `git diff --check`: **passed**.
- Bundled Python module scan against existing configured tokens: **no tokens found**. No private configuration was bundled.
- Live Notion access: both the old API and the updated data-source client successfully read the existing database; expected schema and entry-number lookup verified.
- Save payloads, duplicate rejection, chronology, API errors, timeouts and first-run setup were verified using isolated tests. No live Notion records were created or modified.

## Release

`dist/QOL-Score-macOS-arm64.zip` (approximately 30 MB).

SHA-256: `762ee79ebe3f2968594dc557dc0e4b47ce0de5ab9cb0a1ba488d609ad0b7e2ee`

Minimum supported target for this bundle: macOS 14, Apple Silicon. Actual tests were on the development Mac, including the clean-home simulation. A separate physical recipient Mac, Intel hardware, and live record creation have not been tested. Follow SETUP.md's recipient test before broader distribution. Tokens in historical Git commits were not rewritten or revoked.
