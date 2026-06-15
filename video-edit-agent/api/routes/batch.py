"""批量生成路由 — 文案生成(Phase 1) / SSE / 视频渲染(Phase 2) / 取消 / 历史"""

from __future__ import annotations

import asyncio
import json
import queue as stdlib_queue
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from api.schemas import (
    BatchCancelResponse,
    BatchHistoryResponse,
    BatchPreviewRequest,
    BatchStartResponse,
    BatchStatusResponse,
    GenerateScriptsRequest,
    GenerateScriptsResponse,
    RegenerateScriptRequest,
    RegenerateScriptResponse,
    SaveScriptsRequest,
    ScriptsResponse,
    StartRenderRequest,
    StartRenderResponse,
)
from api.services.progress_manager import manager as pm
from api.services.pipeline import generate_scripts, render_videos
from core.folder_reader import scan_material_folder

router = APIRouter(tags=["batch"])

# SSE 心跳间隔（秒）：防止浏览器/代理断开空闲连接
_SSE_KEEPALIVE_INTERVAL = 25


# ---------------------------------------------------------------------------
# Phase 1 — 文案生成
# ---------------------------------------------------------------------------


@router.post("/batch/generate-scripts", response_model=GenerateScriptsResponse)
async def batch_generate_scripts(body: GenerateScriptsRequest):
    """Phase 1: 扫描卖点组合，后台逐条生成文案"""
    try:
        folder_info = scan_material_folder(body.folder_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"素材文件夹结构错误: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"扫描素材失败: {e}")

    batch_id = pm.create_batch()

    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None,
        generate_scripts,
        folder_info,
        body.count,
        batch_id,
        body.product_name,
        body.usage_scenario,
    )

    return GenerateScriptsResponse(batch_id=batch_id, total=body.count)


# ---------------------------------------------------------------------------
# 重新生成单条文案
# ---------------------------------------------------------------------------


@router.post("/batch/regenerate-script", response_model=RegenerateScriptResponse)
async def regenerate_script(body: RegenerateScriptRequest):
    """重新生成单条文案 — 用户审核时对不满意的文案重新生成"""
    from core.copywriter import generate_script

    try:
        sections = generate_script(
            body.selling_points,
            product_name=body.product_name,
            usage_scenario=body.usage_scenario,
        )
        return RegenerateScriptResponse(
            video_index=body.video_index,
            selling_points=body.selling_points,
            sections=sections,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"文案生成失败: {e}")


# ---------------------------------------------------------------------------
# Phase 2 — 视频渲染（TTS + 剪辑）
# ---------------------------------------------------------------------------


@router.post("/batch/start-render", response_model=StartRenderResponse)
async def batch_start_render(body: StartRenderRequest):
    """Phase 2: 用户确认文案后，启动 TTS → 视频拼接"""
    # 校验 batch 仍然存在
    q = pm.get_queue(body.batch_id)
    if q is None:
        raise HTTPException(status_code=404, detail="Batch 不存在或已过期，请重新生成文案")

    # 重新扫描素材信息
    try:
        folder_info = scan_material_folder(body.folder_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"素材文件夹结构错误: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"扫描素材失败: {e}")

    scripts_data = [
        {
            "video_index": s.video_index,
            "selling_points": s.selling_points,
            "sections": s.sections,
        }
        for s in body.scripts
    ]

    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None,
        render_videos,
        scripts_data,
        body.output_path,
        body.batch_id,
        folder_info,
    )

    return StartRenderResponse(status="started", total=len(body.scripts))


# ---------------------------------------------------------------------------
# 预览卖点组合
# ---------------------------------------------------------------------------


@router.post("/batch/preview")
async def preview_batch(body: BatchPreviewRequest):
    """预览卖点组合 — 不启动生成，只返回每条视频的卖点分配"""
    from core.copywriter import get_all_combinations

    try:
        folder_info = scan_material_folder(body.folder_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"素材文件夹结构错误: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"扫描素材失败: {e}")

    selling_points = folder_info.get("selling_points", [])
    if len(selling_points) < 2:
        raise HTTPException(status_code=400, detail="卖点数量不足 2 个，无法组合")

    all_combos = get_all_combinations(selling_points)
    if not all_combos:
        raise HTTPException(status_code=400, detail="无法生成卖点组合")

    combinations = []
    for i in range(1, body.count + 1):
        combo = all_combos[(i - 1) % len(all_combos)]
        combinations.append({
            "video_index": i,
            "selling_points": list(combo),
        })

    return {
        "combinations": combinations,
        "total_combos": len(all_combos),
        "total_videos": body.count,
    }


# ---------------------------------------------------------------------------
# SSE 进度流（Phase 1 + Phase 2 共用）
# ---------------------------------------------------------------------------


@router.get("/batch/{batch_id}/progress")
async def stream_progress(batch_id: str):
    """SSE 事件流 — 实时获取文案生成 / 视频渲染进度"""
    q = pm.get_queue(batch_id)
    if q is None:
        raise HTTPException(status_code=404, detail="Batch 不存在或已过期")

    async def event_generator():
        loop = asyncio.get_event_loop()
        last_event_time = time.time()

        while True:
            # 使用超时轮询：防止线程永久阻塞 + 支持心跳
            try:
                event_type, data = await loop.run_in_executor(
                    None, lambda: q.get(timeout=_SSE_KEEPALIVE_INTERVAL),
                )
                last_event_time = time.time()
            except stdlib_queue.Empty:
                # 超时无事件：检查客户端是否还连着 + 发心跳保活
                try:
                    yield "event: ping\ndata: {}\n\n"
                except GeneratorExit:
                    break
                except Exception:
                    # yield 失败 = 客户端已断开，清理退出
                    break
                continue
            except GeneratorExit:
                break
            except Exception:
                # 包含 CancelledError / RuntimeError 等
                break

            try:
                yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            except Exception:
                # 客户端断开，停止生成
                break

            if event_type in ("complete", "cancel"):
                break
            # scripts_complete 不断开连接，等待 Phase 2

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# 备用：单步启动（旧版，保留兼容，但功能改由两阶段替代）
# ---------------------------------------------------------------------------


@router.post("/batch/start", response_model=BatchStartResponse)
async def start_batch(body: GenerateScriptsRequest):
    """（兼容）等同于 generate-scripts"""
    from core.copywriter import get_all_combinations

    try:
        folder_info = scan_material_folder(body.folder_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"素材文件夹结构错误: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"扫描素材失败: {e}")

    all_combos = get_all_combinations(folder_info.get("selling_points", []))
    return BatchStartResponse(
        batch_id="",
        total_videos=body.count,
        status="deprecated",
    )


# ---------------------------------------------------------------------------
# 状态 / 取消 / 历史
# ---------------------------------------------------------------------------


@router.get("/batch/{batch_id}/status", response_model=BatchStatusResponse)
async def batch_status(batch_id: str):
    """查询指定 batch 的状态"""
    q = pm.get_queue(batch_id)
    if q is None:
        for entry in pm.get_history(100):
            if entry["batch_id"] == batch_id:
                return BatchStatusResponse(
                    batch_id=batch_id,
                    status=entry.get("status", "done"),
                    progress={"success": entry.get("success_count", 0), "failed": entry.get("fail_count", 0)},
                )
        raise HTTPException(status_code=404, detail="Batch 不存在")

    return BatchStatusResponse(batch_id=batch_id, status="running")


@router.post("/batch/{batch_id}/cancel", response_model=BatchCancelResponse)
async def cancel_batch(batch_id: str):
    """取消运行中的 batch"""
    q = pm.get_queue(batch_id)
    if q is None:
        raise HTTPException(status_code=404, detail="Batch 不存在或已完成")
    pm.cancel(batch_id)
    return BatchCancelResponse(status="cancelling")


# ---------------------------------------------------------------------------
# 文案实时持久化（独立于队列生命周期）
# ---------------------------------------------------------------------------


@router.put("/batch/{batch_id}/scripts")
async def save_scripts(batch_id: str, body: SaveScriptsRequest):
    """保存文案到文件 — 实时持久化用户编辑的文案内容，页面刷新不丢失"""
    pm.save_scripts(batch_id, [s.model_dump() for s in body.scripts])
    return {"status": "ok"}


@router.get("/batch/{batch_id}/scripts", response_model=ScriptsResponse)
async def load_scripts(batch_id: str):
    """加载已保存的文案 — 无论 batch 是否还在内存中均可读取"""
    scripts = pm.load_scripts(batch_id)
    return ScriptsResponse(scripts=scripts)


@router.get("/batch/history", response_model=BatchHistoryResponse)
async def batch_history(limit: int = 10):
    """获取最近的 batch 运行记录"""
    return BatchHistoryResponse(history=pm.get_history(limit=limit))
