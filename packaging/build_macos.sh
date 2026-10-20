#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${QOL_PYTHON:-python3}"
"$PYTHON" -c 'import sys, tkinter; assert sys.platform == "darwin", "Build the Mac app on macOS"; assert sys.version_info >= (3, 11), "Use Python 3.11 or newer"'
"$PYTHON" -m PyInstaller --noconfirm packaging/QOL_Score.spec
ARCH="$("$PYTHON" -c 'import platform; print(platform.machine())')"
/usr/bin/ditto -c -k --sequesterRsrc --keepParent 'dist/QOL Score.app' "dist/QOL-Score-macOS-${ARCH}.zip"
printf 'Built dist/QOL-Score-macOS-%s.zip\n' "$ARCH"
