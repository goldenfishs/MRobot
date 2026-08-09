# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path


version_namespace = {}
exec(Path('app/_version.py').read_text(encoding='utf-8'), version_namespace)
project_version = version_namespace['__version__']


a = Analysis(
    ['MRobot.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('app', 'app'), ('app/tools', 'app/tools'), ('mcode/schemas', 'mcode/schemas')],
    hiddenimports=['mcode', 'mcode.stm32', 'mcode.legacy', 'mcode.registry'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

if sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='MRobot',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    contents = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        name='MRobot',
    )
    app = BUNDLE(
        contents,
        name='MRobot.app',
        icon='assets/logo/MRobot.icns',
        bundle_identifier='org.mrobot.desktop',
        info_plist={
            'CFBundleDisplayName': 'MRobot',
            'CFBundleShortVersionString': project_version,
            'CFBundleVersion': project_version,
            'LSMinimumSystemVersion': '11.0',
            'NSHighResolutionCapable': True,
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='MRobot',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        icon='assets/logo/MRobot.ico' if sys.platform == 'win32' else None,
        codesign_identity=None,
        entitlements_file=None,
    )
