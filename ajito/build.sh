#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
QOL_BUILD_PYTHON="${QOL_PYTHON:-python3}"
"$QOL_BUILD_PYTHON" -m PyInstaller --noconfirm ajito/Service.spec
APP='dist/QOL Score Ajito.app'
# A release must not retain deleted files from an earlier build.
rm -rf -- "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
/usr/bin/ditto 'dist/QOLService' "$APP/Contents/Resources/backend"
cp ajito/smoke.js "$APP/Contents/Resources/smoke.js"
cp ajito/read-check.js "$APP/Contents/Resources/read-check.js"
cp ajito/setup-check.js "$APP/Contents/Resources/setup-check.js"
cp ajito/Ajito.icns "$APP/Contents/Resources/Ajito.icns"
xcrun clang -fobjc-arc -O2 -arch arm64 -mmacosx-version-min=11.1 ajito/native/Ajito.m -o "$APP/Contents/MacOS/QOL Ajito" -framework Cocoa -framework WebKit -framework UniformTypeIdentifiers
"$QOL_BUILD_PYTHON" - <<'PY'
import plistlib
from pathlib import Path
info={'CFBundleName':'QOL Score Ajito','CFBundleDisplayName':"QOL Score · Boyacky's Ajito",'CFBundleExecutable':'QOL Ajito','CFBundleIdentifier':'com.qolscore.ajito','CFBundlePackageType':'APPL','CFBundleVersion':'4','CFBundleShortVersionString':'2.0.2','LSMinimumSystemVersion':'11.1','NSHighResolutionCapable':True,'NSAppTransportSecurity':{'NSAllowsLocalNetworking':True},'NSPrincipalClass':'NSApplication','CFBundleIconFile':'Ajito.icns'}
Path('dist/QOL Score Ajito.app/Contents/Info.plist').write_bytes(plistlib.dumps(info))
PY
/usr/bin/codesign --force --deep --sign - "$APP"
/usr/bin/codesign --verify --deep --strict "$APP"
"$QOL_BUILD_PYTHON" ajito/verify.py "$APP"
/usr/bin/ditto -c -k --sequesterRsrc --keepParent "$APP" dist/QOL-Score-Ajito-v2.0.2-macOS-arm64.zip
