# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all

site_packages = os.path.join(sys.prefix, 'Lib', 'site-packages')

datas = []
binaries = []
hiddenimports = []
tmp_ret = collect_all('paddleocr')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

models = [
    ('_internal/models/cls', 'models/cls'),

    ('_internal/models/det', 'models/det'),

    ('_internal/models/rec', 'models/rec'),
]

paddle_dll_path = os.path.join(site_packages, 'paddle', 'libs')
paddle_dlls = [
    (paddle_dll_path, '.'),
]

datas += models
datas += [('_internal/ocr.png', '.')]
binaries += paddle_dlls

# 直接复制整个Cython目录
cython_dir = os.path.join(site_packages, 'Cython')
if os.path.exists(cython_dir):
    for root, dirs, files in os.walk(cython_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(os.path.dirname(file_path), site_packages)
            datas.append((file_path, rel_path))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OCR-Tool',
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
    icon=['_internal/ocr.png'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OCR-Tool',
)
