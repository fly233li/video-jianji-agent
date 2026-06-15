"""视频转码路由 — scan + start + SSE progress"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from api.services.progress_manager import manager as pm
from core.transcoder import scan_mov_files, batch_transcode

router = APIRouter(tags=["transcode"])


# ---------------------------------------------------------------------------
# 请求/响应模型
# ---------------------------------------------------------------------------

class ScanRequest(BaseModel):
    path: str


class ScanResponse(BaseModel):
    files: list[dict]
    total: int


class StartRequest(BaseModel):
    input_folder: str
    output_folder: str


class StartResponse(BaseModel):
    job_id: str
    total: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/transcode/scan", response_model=ScanResponse)
async def scan_folder(body: ScanRequest):
    """扫描文件夹中的 .MOV 文件"""
    try:
        files = scan_mov_files(body.path)
        return ScanResponse(files=files, total=len(files))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"扫描失败: {e}")


@router.post("/transcode/start", response_model=StartResponse)
async def start_transcode(body: StartRequest):
    """启动批量转码任务（后台线程）"""
    import os

    if not os.path.isdir(body.input_folder):
        raise HTTPException(status_code=400, detail="输入文件夹不存在")
    if not os.path.isdir(body.output_folder):
        raise HTTPException(status_code=400, detail="输出文件夹不存在")

    try:
        files = scan_mov_files(body.input_folder)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"扫描失败: {e}")

    job_id = pm.create_batch()

    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None,
        batch_transcode,
        body.input_folder,
        body.output_folder,
        job_id,
        pm,
    )

    return StartResponse(job_id=job_id, total=len(files))


@router.get("/transcode/{job_id}/progress")
async def transcode_progress(job_id: str):
    """SSE 实时进度流"""
    q = pm.get_queue(job_id)
    if q is None:
        return StreamingResponse(
            _error_stream("任务不存在或已结束"),
            media_type="text/event-stream",
        )

    async def event_generator():
        loop = asyncio.get_event_loop()
        try:
            while True:
                event_type, data = await loop.run_in_executor(None, q.get)
                yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                if event_type in ("complete", "cancel"):
                    break
        except Exception:
            yield f"event: error\ndata: {json.dumps({'message': '连接中断'})}\n\n"
        finally:
            # 延迟清理队列，确保客户端能收到最后一条事件
            await asyncio.sleep(5)
            pm.remove_queue(job_id)
            pm.clear_cancelled(job_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _error_stream(message: str):
    """返回一个简单的 SSE 错误流"""
    data = json.dumps({"message": message}, ensure_ascii=False)
    yield f"event: error\ndata: {data}\n\n"
    yield f"event: complete\ndata: {json.dumps({'status': 'error'})}\n\n"
