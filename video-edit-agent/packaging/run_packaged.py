"""打包后的入口脚本 — 处理路径并启动服务"""
import os
import sys
from pathlib import Path

# 确定运行根目录
if getattr(sys, 'frozen', False):
    # onedir 模式：sys._MEIPASS 指向 _internal/，数据文件在 dist 根目录
    BASE_DIR = Path(sys._MEIPASS).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

# 将 dist 根目录加入 sys.path（用于 import config.py 等）
sys.path.insert(0, str(BASE_DIR))

# 确保 ffmpeg 在 PATH 中
ffmpeg_dir = str(BASE_DIR)
path = os.environ.get('PATH', '')
if ffmpeg_dir not in path:
    os.environ['PATH'] = ffmpeg_dir + os.pathsep + path

# 显式导入，确保 PyInstaller 静态分析能追踪到 api 模块
import api.app  # noqa: F401

# 启动服务
import uvicorn

print(f"  [OK] 工作目录: {BASE_DIR}")
print(f"  [OK] 启动服务: http://localhost:8000")
print(f"  [OK] 按 Ctrl+C 停止服务")
print()

uvicorn.run(
    "api.app:app",
    host="127.0.0.1",
    port=8000,
    log_level="info",
)
