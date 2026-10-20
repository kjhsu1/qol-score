from pathlib import Path
from PyInstaller.utils.hooks import collect_all
root=Path(SPECPATH).parent
tz_data,tz_binaries,tz_imports=collect_all('tzdata')
a=Analysis([str(root/'ajito/service.py')],pathex=[str(root/'For_new_users/Scripts')],binaries=tz_binaries,
    datas=tz_data+[(str(root/'ajito/web'),'ajito/web')],
    hiddenimports=tz_imports,excludes=['matplotlib','numpy','PIL','IPython','pytest','pandas','scipy','tkinter','_tkinter'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='QOLService',console=True,strip=False,upx=False)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='QOLService')
