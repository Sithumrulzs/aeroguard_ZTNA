# aeroguard_terminal.spec
# Run:  pyinstaller aeroguard_terminal.spec --noconfirm --clean

block_cipher = None

a = Analysis(
    ['aeroguard_terminal.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter', 'tkinter.scrolledtext', 'tkinter.font',
        'socket', 'threading', 'urllib.request', 'urllib.error',
        'sqlite3', 'json', 'webbrowser',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
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
    name='AeroGuard_Terminal',
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # no black console window — GUI only
    icon=None,          # replace with 'aeroguard.ico' if you have one
)
