#!/usr/bin/env python3
"""Reject Mac bundles with missing assets or developer-machine dependencies."""
import json
from pathlib import Path
import plistlib
import platform
import re
import subprocess
import sys


def verify(app):
    app = Path(app).resolve()
    info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
    minimum = tuple(map(int, info['LSMinimumSystemVersion'].split('.')))
    failures = []
    architectures = set()
    expected_arch = platform.machine()
    count = 0
    for path in app.rglob('*'):
        if path.is_symlink():
            if not path.exists():
                failures.append(f'Broken bundle link: {path.relative_to(app)}')
            continue
        if not path.is_file():
            continue
        with path.open('rb') as stream:
            magic = stream.read(4)
        if magic not in (b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca'):
            continue
        count += 1
        label = str(path.relative_to(app))
        arch = subprocess.check_output(['/usr/bin/lipo', '-archs', str(path)], text=True).split()
        architectures.update(arch)
        if expected_arch not in arch:
            failures.append(f'No {expected_arch} code: {label}')
        loads = subprocess.check_output(['/usr/bin/otool', '-L', str(path)], text=True)
        for line in loads.splitlines()[1:]:
            dependency = line.strip().split(' (', 1)[0]
            if dependency.startswith('/') and not dependency.startswith(('/usr/lib/', '/System/Library/')):
                failures.append(f'External library in {label}: {dependency}')
            if dependency.startswith('@loader_path/'):
                target = path.parent / dependency.removeprefix('@loader_path/')
                if not target.exists():
                    failures.append(f'Missing library in {label}: {dependency}')
        commands = subprocess.check_output(['/usr/bin/otool', '-l', str(path)], text=True)
        versions = re.findall(r'\bminos\s+(\d+(?:\.\d+)+)', commands)
        versions += re.findall(r'cmd LC_VERSION_MIN_MACOSX\s+cmdsize \d+\s+version (\d+(?:\.\d+)+)', commands)
        for version in versions:
            found = tuple(map(int, version.split('.')))
            if (found + (0, 0, 0))[:3] > (minimum + (0, 0, 0))[:3]:
                failures.append(f'{label} requires macOS {version}, advertised minimum is {info["LSMinimumSystemVersion"]}')
    resources = app / 'Contents/Resources'
    for resource in ('tzdata/zoneinfo/America/Los_Angeles', 'tzdata/zoneinfo/Asia/Tokyo',
                     'certifi/cacert.pem', '_tcl_data/init.tcl', '_tk_data/tk.tcl',
                     'Images/pixel_smile_background.png', 'Images/boyyaky.jpg',
                     'Images/boyyaky_button.png', 'Images/kabu_chart_man_happy.jpg',
                     'Images/jyaian.jpg', 'Images/yugioh.jpg', 'Images/mail.jpg',
                     'Images/medalist.jpeg'):
        if not (resources / resource).is_file():
            failures.append('Missing resource: ' + resource)
    if not count:
        failures.append('No executable code found')
    signing = subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(app)],
                             capture_output=True, text=True)
    if signing.returncode:
        failures.append('Signature verification failed: ' + signing.stderr.strip())
    return {'ok': not failures, 'version': info['CFBundleShortVersionString'],
            'minimum_macos': info['LSMinimumSystemVersion'], 'architectures': sorted(architectures),
            'mach_o_files_checked': count, 'errors': failures}


if __name__ == '__main__':
    report = verify(sys.argv[1] if len(sys.argv) > 1 else 'dist/QOL Score.app')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['ok'] else 1)
