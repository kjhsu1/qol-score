# Build on each architecture; never bundle config files or personal credentials.
from pathlib import Path
root = Path(SPECPATH).parent
analysis = Analysis(
    [str(root / 'For_new_users' / 'launch.py')],
    pathex=[str(root / 'For_new_users' / 'Scripts')],
    binaries=[],
    datas=[(str(root / 'For_new_users' / 'Images'), 'Images'),
           (str(root / 'For_new_users' / 'Text_Files'), 'Text_Files')],
    hiddenimports=['UI', 'ranking', 'core', 'config', 'notion_client', 'QOL_LIB', 'PIL._tkinter_finder', 'self_test'],
    excludes=['pytest', 'IPython', 'notebook', 'scipy', 'pandas'],
    hooksconfig={'matplotlib': {'backends': ['TkAgg']}},
    noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(pyz, analysis.scripts, [], exclude_binaries=True, name='QOL Score',
          debug=False, strip=False, upx=False, console=False)
collect = COLLECT(exe, analysis.binaries, analysis.datas, strip=False, upx=False, name='QOL Score')
app = BUNDLE(collect, name='QOL Score.app', bundle_identifier='com.qolscore.desktop',
             info_plist={'CFBundleShortVersionString': '1.1.0', 'NSHighResolutionCapable': True, 'LSMinimumSystemVersion': '14.0'})
