# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['standalone_app.py'],
    pathex=['C:\\Users\\sadma\\Desktop\\image resizer'],
    binaries=[],
    datas=[
        ('image_resizer.py', '.'),
        ('config.py', '.'),
    ],
    hiddenimports=[
        'PIL',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'concurrent.futures',
        'threading',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'streamlit',
        'numpy',
        'pandas',
        'plotly',
        'altair',
        'tornado',
        'click',
        'watchdog',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ImageResizer',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)