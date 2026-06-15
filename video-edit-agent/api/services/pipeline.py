"""后台批处理流水线 — 分两阶段：文案生成 → TTS + 视频渲染"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from api.services.progress_manager import manager as pm


def generate_scripts(
    folder_info: dict[str, Any],
    count: int,
    batch_id: str,
    product_name: str = "",
    usage_scenario: str = "",
):
    """Phase 1: 遍历卖点组合，逐条生成文案（不涉及 TTS / 视频）"""
    from core.copywriter import generate_script as gen_script, get_all_combinations

    all_combos = get_all_combinations(folder_info["selling_points"])

    pm.push_event(batch_id, "log", {
        "message": f"共 {len(all_combos)} 种卖点组合可用，开始生成文案...",
    })

    for i in range(1, count + 1):
        if pm.is_cancelled(batch_id):
            pm.push_event(batch_id, "cancel", {"message": "用户中断"})
            return

        combo = all_combos[(i - 1) % len(all_combos)]

        pm.push_event(batch_id, "script_start", {
            "video_index": i,
            "total": count,
            "selling_points": list(combo),
        })

        try:
            from core.copywriter import generate_script
            sections = generate_script(
                combo,
                product_name=product_name,
                usage_scenario=usage_scenario,
            )

            pm.push_event(batch_id, "script", {
                "video_index": i,
                "selling_points": list(combo),
                "sections": sections,
            })

            pm.push_event(batch_id, "log", {
                "message": f"  [{i}/{count}] 文案生成完成: {combo[0]} + {combo[1]}",
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            pm.push_event(batch_id, "script_error", {
                "video_index": i,
                "selling_points": list(combo),
                "message": str(e),
            })

    pm.push_event(batch_id, "scripts_complete", {
        "total": count,
        "message": "所有文案已生成，请检查并编辑",
    })


def render_videos(
    scripts: list[dict[str, Any]],
    output_path: str,
    batch_id: str,
    folder_info: dict[str, Any],
):
    """Phase 2: 用用户确认后的文案逐条合成语音 → 剪辑视频"""
    from core.copywriter import split_into_segments
    from core.tts_engine import generate_tts
    from core.video_assembler import VideoAssembler

    os.makedirs(output_path, exist_ok=True)

    def progress_callback(msg: str):
        pm.push_event(batch_id, "log", {"message": msg})

    assembler = VideoAssembler(folder_info, progress_callback=progress_callback)
    total = len(scripts)
    success_count = 0
    fail_count = 0
    batch_start = time.time()

    for item in scripts:
        video_index = item["video_index"]
        sections = item["sections"]
        combo = item["selling_points"]

        if pm.is_cancelled(batch_id):
            pm.push_event(batch_id, "cancel", {"message": "用户中断"})
            break

        pm.push_event(batch_id, "video_start", {
            "video_index": video_index,
            "total": total,
            "selling_points": list(combo),
        })

        video_start = time.time()
        video_path = os.path.join(output_path, f"output_{video_index:03d}.mp4")

        try:
            pm.push_event(batch_id, "log", {
                "message": f"  [{video_index}/{total}] 正在分镜切分...",
            })
            segments = split_into_segments(sections)

            pm.push_event(batch_id, "log", {
                "message": f"  [{video_index}/{total}] 正在合成语音...",
            })
            tts_data = generate_tts(sections)

            pm.push_event(batch_id, "log", {
                "message": f"  [{video_index}/{total}] 正在剪辑视频...",
            })
            assembler.assemble(
                sections=sections,
                tts_data=tts_data,
                output_path=video_path,
                chosen_two=combo,
                video_index=video_index,
                segments=segments,
            )

            elapsed = time.time() - video_start

            # ── 生成配套剪映草稿 ────────────────────────────────────
            try:
                draft_base_dir = os.path.join(output_path, "..", "drafts")
                draft_base_dir = os.path.normpath(draft_base_dir)
                draft_name = os.path.splitext(os.path.basename(video_path))[0]

                from core.jianying_draft import generate_draft
                generate_draft(
                    draft_name=draft_name,
                    draft_base_dir=draft_base_dir,
                    sec_data=assembler.sec_data,
                    tts_data=tts_data,
                    sections=sections,
                    segments=segments,
                    folder_info=folder_info,
                )
                pm.push_event(batch_id, "log", {
                    "message": f"  [{video_index}/{total}] 剪映草稿已生成 → {draft_name}",
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                pm.push_event(batch_id, "log", {
                    "message": f"  [{video_index}/{total}] 剪映草稿生成失败: {e}",
                })

            success_count += 1

            pm.push_event(batch_id, "video_done", {
                "video_index": video_index,
                "output_path": video_path,
                "elapsed": round(elapsed, 1),
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            fail_count += 1
            pm.push_event(batch_id, "error", {
                "video_index": video_index,
                "message": str(e),
            })

    # 清理
    try:
        assembler.cleanup()
    except Exception:
        pass

    total_time = time.time() - batch_start

    pm.add_history({
        "batch_id": batch_id,
        "status": "done",
        "total_videos": total,
        "success_count": success_count,
        "fail_count": fail_count,
        "total_time": round(total_time, 1),
        "output_path": output_path,
        "folder_path": folder_info.get("root", ""),
        "started_at": batch_start,
    })

    pm.push_event(batch_id, "complete", {
        "total_videos": total,
        "success": success_count,
        "failed": fail_count,
        "total_time": round(total_time, 1),
    })

    time.sleep(5)
    pm.remove_queue(batch_id)
