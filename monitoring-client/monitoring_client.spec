# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for VibgyorSeek Employee Monitoring Client

This spec file configures PyInstaller to create a standalone Windows executable
that includes all dependencies and can run as a Windows service.

Requirements: 14.1, 14.2
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all submodules from src package
src_hiddenimports = collect_submodules('src')

# Additional hidden imports that PyInstaller might miss
hiddenimports = [
    'win32timezone',
    'win32api',
    'win32con',
    'win32event',
    'win32evtlogutil',
    'win32service',
    'win32serviceutil',
    'servicemanager',
    'win32security',
    'ntsecuritycon',
    'pywintypes',
    'PIL._tkinter_finder',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'pynput.keyboard',
    'pynput.mouse',
    'pynput.keyboard._win32',
    'pynput.mouse._win32',
    'psutil',
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'dotenv',
    'lz4',
    'lz4.frame',
] + src_hiddenimports

# Data files to include
datas = [
    ('.env.example', '.'),  # Include example config
]

# Binaries - PyInstaller should auto-detect most, but we can specify critical ones
binaries = []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'hypothesis',
        'test',
        'tests',
        'testing',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VibgyorSeekMonitoring',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for service mode compatibility
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file path here if available
    version_file=None,  # Add version info file here if needed
    uac_admin=False,  # Don't require admin by default (service install will need admin)
    uac_uiaccess=False,
)
