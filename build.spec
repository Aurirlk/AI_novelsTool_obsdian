# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置（Windows 桌面应用）
# 用法：pip install pyinstaller
#      pyinstaller build.spec
# 产物：dist/AI网文编辑器/AI网文编辑器.exe

a = Analysis(
    ['src/run_complete.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('skills', 'skills'),
        ('mcp_servers.json', '.'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'openai',
        'docx',
        'win32com',
        'dotenv',
        'src.mcp.client',
        'src.mcp.manager',
        'src.mcp.config',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'pytest', 'PyQt6.QtWebEngineWidgets'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI网文编辑器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # GUI 应用，不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI网文编辑器',
)
