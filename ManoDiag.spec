# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules
import os

block_cipher = None
hiddenimports = collect_submodules('PyQt6')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('logo_ManoDiag.png', '.'),
        ('exemple.manodiag.json', '.'),
        ('app.ico', '.'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tests',
        'tkinter',
        'unittest',
        'distutils',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Si tu veux réactiver la version: ajouter version='version.txt' et créer le fichier
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ManoDiag',
    icon='app.ico',
    console=False,
    disable_windowed_traceback=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=os.environ.get('UPX_AVAILABLE', '0') == '1',
    name='ManoDiag'
)
