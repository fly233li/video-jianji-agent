# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 — 视频剪辑助手（onedir 模式）
用法: cd 项目根目录 && pyinstaller packaging/build.spec
"""
import os
import sys
from pathlib import Path

block_cipher = None

# 项目根目录
PROJECT = Path(r"E:\AI_jianji\video-edit-agent")

# FFmpeg 路径（此路径下的 ffmpeg.exe / ffprobe.exe 会被自动收集为 binaries）
FFMPEG_DIR = Path(r"C:\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\bin")

# 入口脚本
ENTRY_SCRIPT = str(PROJECT / "packaging" / "run_packaged.py")

# ---------------------------------------------------------------------------
# Analysis — 分析所有 Python 依赖
# ---------------------------------------------------------------------------
a = Analysis(
    [ENTRY_SCRIPT],
    pathex=[str(PROJECT)],
    binaries=[],
    datas=[],  # 数据文件由 build.bat 后处理复制
    hiddenimports=[
        'api.app',
        'api.routes.config',
        'api.routes.project',
        'api.routes.batch',
        'api.routes.transcode',
        'core.video_assembler',
        'core.copywriter',
        'core.tts_engine',
        'core.subtitle_gen',
        'core.transcoder',
        'uvicorn',
        'uvicorn.loggers',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.middleware',
        'uvicorn.workers',
        'fastapi',
        'starlette.routing',
        'starlette.middleware',
        'starlette.staticfiles',
        'starlette.responses',
        'starlette.requests',
        'pydantic',
        'pydantic.color',
        'pydantic.types',
        'importlib',
        'queue',
        'asyncio',
        'concurrent',
        'concurrent.futures',
        'threading',
        'xml',
        'xml.etree',
        'xml.etree.ElementTree',
        'openai',
        'edge_tts',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    excludes=[
        'config',  # 以 data 文件置于根目录，便于读写
        'tkinter',
        'matplotlib',
        'PIL', 'Pillow',
        'scipy', 'pandas',
        'tensorflow', 'torch',
        'PyQt5', 'PySide6',
        'notebook', 'ipython', 'jupyter',
        'setuptools', 'pip', 'wheel',
        'packaging',
    ],
)

# ---------------------------------------------------------------------------
# PYZ
# ---------------------------------------------------------------------------
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ---------------------------------------------------------------------------
# EXE — 可执行文件（不含 data/binaries，只有 bootloader + 脚本）
# ---------------------------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='VideoEditAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    icon=str(PROJECT / 'logo.ico'),
)

# ---------------------------------------------------------------------------
# COLLECT — 将所有文件收集到 dist/视频剪辑助手/ 目录
# ---------------------------------------------------------------------------
collect = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='视频剪辑助手',
)
