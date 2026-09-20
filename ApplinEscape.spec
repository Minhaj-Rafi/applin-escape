# Build on Windows with: python -m PyInstaller --noconfirm ApplinEscape.spec
from pathlib import Path
root = Path(SPECPATH)
a = Analysis([str(root / 'launch.py')], pathex=[str(root)],
             binaries=[], datas=[(str(root / 'assets'), 'assets')],
             hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='ApplinEscape',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='ApplinEscape')
