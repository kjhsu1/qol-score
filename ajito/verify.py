"""Validate an Ajito release without assuming developer files exist on recipients."""
import json
from pathlib import Path
import plistlib
import re
import subprocess
import sys


def verify(path):
    root=Path(path).resolve();info=plistlib.loads((root/'Contents/Info.plist').read_bytes())
    minimum=tuple(map(int,info['LSMinimumSystemVersion'].split('.')))
    issues=[];count=0
    for p in root.rglob('*'):
        if p.is_symlink():
            if not p.exists():issues.append('Broken link: '+str(p.relative_to(root)))
            continue
        if not p.is_file():continue
        with p.open('rb') as f:magic=f.read(4)
        if magic not in (b'\xcf\xfa\xed\xfe',b'\xca\xfe\xba\xbe'):continue
        count+=1;label=str(p.relative_to(root))
        arch=subprocess.check_output(['/usr/bin/lipo','-archs',str(p)],text=True).split()
        if 'arm64' not in arch:issues.append('No arm64 code: '+label)
        load=subprocess.check_output(['/usr/bin/otool','-l',str(p)],text=True)
        versions=re.findall(r'\bminos\s+(\d+(?:\.\d+)+)',load)+re.findall(r'cmd LC_VERSION_MIN_MACOSX\s+cmdsize \d+\s+version (\d+(?:\.\d+)+)',load)
        for v in versions:
            found=tuple(map(int,v.split('.')))
            if (found+(0,0,0))[:3]>(minimum+(0,0,0))[:3]:issues.append(f'{label} requires {v}, above advertised OS')
        deps=subprocess.check_output(['/usr/bin/otool','-L',str(p)],text=True)
        for line in deps.splitlines()[1:]:
            dep=line.strip().split(' (',1)[0]
            if dep.startswith('/') and not dep.startswith(('/usr/lib/','/System/Library/')):issues.append('External dependency: '+dep)
            if dep.startswith('@loader_path/') and not (p.parent/dep.removeprefix('@loader_path/')).exists():issues.append('Missing dependency: '+dep)
    internal=root/'Contents/Resources/backend/_internal'
    for relative in ('tzdata/zoneinfo/America/Los_Angeles','tzdata/zoneinfo/Asia/Tokyo','tzdata/zoneinfo/Europe/London','certifi/cacert.pem','ajito/web/index.html','ajito/web/app.js','ajito/web/style.css','ajito/web/mascot.js','ajito/web/vendor/three.module.min.js','ajito/web/assets/ajito.png','ajito/web/assets/ajito-banner-bold.ttf','ajito/web/assets/NOTO-OFL.txt'):
        if not (internal/relative).is_file():issues.append('Missing resource: '+relative)
    if not (root/'Contents/Resources/backend/QOLService').is_file():issues.append('Missing service')
    if list(root.rglob('config.json')) or list(root.rglob('config.local.json')):issues.append('Private configuration included')
    sign=subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',str(root)],capture_output=True,text=True)
    if sign.returncode:issues.append('Invalid signature: '+sign.stderr)
    return {'ok':not issues,'native_binaries':count,'architecture':'arm64','minimum_macos':info['LSMinimumSystemVersion'],'errors':issues}


if __name__=='__main__':
    result=verify(sys.argv[1] if len(sys.argv)>1 else 'dist/QOL Score Ajito.app')
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['ok'] else 1)
