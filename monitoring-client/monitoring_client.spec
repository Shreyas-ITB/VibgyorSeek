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

# Explicitly list all src modules to ensure they're included
src_modules = [
    'src',
    'src.activity_tracker',
    'src.app_monitor',
    'src.app_usage_tracker',
    'src.browser_monitor',
    'src.browser_tab_usage_tracker',
    'src.config',
    'src.config_watcher',
    'src.file_sync_manager',
    'src.http_transmitter',
    'src.location_tracker',
    'src.logger',
    'src.monitoring_loop',
    'src.payload_builder',
    'src.queue_manager',
    'src.retry_manager',
    'src.screenshot',
    'src.server_env_watcher',
    'src.service_manager',
]

# Additional hidden imports that PyInstaller might miss
hiddenimports = [
    'psutil',
    'psutil._pswindows',
    'PIL._tkinter_finder',
    'PIL.Image',
    'PIL.ImageGrab',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'pynput',
    'pynput.keyboard',
    'pynput.mouse',
    'pynput.keyboard._win32',
    'pynput.mouse._win32',
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'dotenv',
    'lz4',
    'lz4.frame',
    'geocoder',
    'watchdog',
    'watchdog.observers',
    'watchdog.observers.winapi',
    'win32api',
    'win32con',
    'win32gui',
    'win32process',
    'win32clipboard',
    'pywintypes',
    'logging.handlers',
] + src_modules

# Data files to include
datas = [
    ('.env.example', '.'),  # Include example config
    ('src', 'src'),  # Include entire src directory
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
        'pkg_resources',
        'setuptools',
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
    console=False,  # Run without console window (background mode)
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
