# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from os import path

block_cipher = None

# Root path dari project
PROJ_PATH = os.getcwd()  # Menggunakan current working directory sebagai gantinya

a = Analysis(
    ['src/gui.py'],  # Sesuaikan dengan path file utama
    pathex=[PROJ_PATH],
    binaries=[
        # Sesuaikan path ffmpeg sesuai instalasi di komputer Anda
        ('C:\\ffmpeg\\bin\\ffmpeg.exe', '.'),
        ('C:\\ffmpeg\\bin\\ffprobe.exe', '.'),
    ],
    datas=[
        # Tambahkan file-file static jika ada
        ('README.md', '.'),
        ('assets/*', 'assets'),  # Jika ada folder assets
    ],
    hiddenimports=[
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'psutil',
        'concurrent.futures',
        'logging',
        'json',
        'datetime'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
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
    name='VideoCutter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Biarkan True untuk kompres exe
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    version='file_version_info.txt',
    uac_admin=False,  # Jangan minta akses admin jika tidak perlu
    manifest='manifest.xml'  # Tambahkan manifest
)