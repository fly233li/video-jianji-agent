"""FastAPI 应用实例"""

from __future__ import annotations

import os
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import config as config_router
from api.routes import project as project_router
from api.routes import batch as batch_router
from api.routes import transcode as transcode_router

# ------------------------------------------------------------
# 将 ffmpeg 加入 PATH（优先于系统 PATH），供 subprocess 调用
# 依次检查：内置 dist 目录 > 开发工具目录 > 系统 PATH
# ------------------------------------------------------------
_ffmpeg_candidates = [
    Path(__file__).resolve().parent.parent / "dist" / "视频剪辑助手",
    Path(r"C:\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\bin"),
]
for _d in _ffmpeg_candidates:
    if _d.exists() and (_d / "ffmpeg.exe").exists():
        os.environ["PATH"] = str(_d) + os.pathsep + os.environ.get("PATH", "")
        break


def _check_ffmpeg() -> bool:
    """检查 ffmpeg 是否可用"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    app.state.ffmpeg_available = _check_ffmpeg()
    if not app.state.ffmpeg_available:
        print("  [WARNING] ffmpeg 未找到，视频导出将失败")
    yield


app = FastAPI(
    title="Video Edit Agent",
    description="钢制家具淘宝短视频批量剪辑助手",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — 允许前端开发服务器访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(config_router.router, prefix="/api")
app.include_router(project_router.router, prefix="/api")
app.include_router(batch_router.router, prefix="/api")
app.include_router(transcode_router.router, prefix="/api")


@app.get("/api/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "ffmpeg": app.state.ffmpeg_available,
    }


@app.post("/api/check-llm")
def check_llm():
    """测试 LLM 连通性及延迟（支持 OpenAI / Anthropic 双后端）"""
    import importlib
    import sys

    importlib.reload(sys.modules.get("config", __import__("config")))
    from core.llm import LLMClient

    client = LLMClient()
    return client.check_connectivity()


# 生产模式：提供前端静态文件
if getattr(sys, 'frozen', False):
    _frontend_dist = Path(sys._MEIPASS).parent / "frontend" / "dist"
else:
    _frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(_frontend_dist), html=True),
        name="frontend",
    )


@app.middleware("http")
async def spa_fallback(request, call_next):
    """SPA 降级：非 API 路径的 404 返回 index.html"""
    response = await call_next(request)
    if response.status_code == 404 and not request.url.path.startswith("/api"):
        index_path = _frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path), media_type="text/html")
    return response
