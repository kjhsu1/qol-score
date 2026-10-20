# Verification — 2026-10-19 — version 1.2.0

- Host: Apple Silicon arm64, macOS 26.4, Python 3.11.9.
- Regression suite: **40 tests passed**. Covers scoring, API failures, private configuration, token-free invitations, identity routing, group access checks, and partial rankings.
- Offline bundled GUI test after ZIP extraction to a path containing spaces: **passed**. Includes group invitation import, explicit identity selection, group setup success, cancellation during a pending check without saving, full/partial ranking windows, form scoring, analysis, score display and plotting.
- Code signature: `codesign --verify --deep --strict` **passed** (ad-hoc; no Developer ID or notarization).
- Python syntax and `git diff --check`: **passed**.
- Bundle module scan against configured private tokens: **passed**. Invitation contains no tokens. Source credential-literal scan passed.
- Live read-only follow-up checks: the shared token now passes schema and latest-entry queries for Kenta, Kazuma, and Eoin. The actual ranking fetch succeeded for all three participants. The private local configuration was updated to use that shared token for Kazuma and Eoin, with owner-only backups preserved. No Notion records were changed.
- Setup checks schema and query access only. Insert permission is configured in Notion and must be checked through normal use; no live write was performed.

## Release

`dist/QOL-Score-macOS-arm64.zip`

SHA-256: `fac527d4ba33a0b12c0cdd5e412efa6f41f8708506fbdf3d9668fe2636ec67c6`

Local `dist/QOL-Friends.qol-group.json` is a token-free invitation exported from the existing participant list. It is not committed or bundled. Use a dedicated group token through the setup dialog, never by adding it to that invitation.

This bundle targets Apple Silicon, macOS 14+. Intel hardware and another physical Mac remain untested. Participant discovery is file-based; all members must import an updated invitation when the roster changes. The shared token grants access to participant data, including diaries; this is a trusted-group model, not per-person authentication.
