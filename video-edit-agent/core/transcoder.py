"""视频转码模块 — iPhone .MOV → 标准 .MP4（适配剪辑流水线）

支持两种 iPhone 拍摄格式：
  - H.264 .MOV（较老机型，兼容性好）
  - HEVC .MOV（较新机型，压缩率高）

共同风险：
  VFR（可变帧率）— iPhone 默认 VFR 省电，
  xfade 过渡和 n/fps 运镜表达式依赖恒定帧率

转码策略:
  H.264 + CFR → ffmpeg -c copy 快速 remux（不重新编码）
  其余情况    → 完整重编码：CFR压制 + libx264
  注意：不做任何旋转修正，保留原始像素方向
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def scan_mov_files(folder_path: str) -> list[dict]:
    """递归扫描文件夹下所有 .mov/.MOV 文件"""
    root = Path(folder_path)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"文件夹不存在: {folder_path}")

    files = []
    for f in sorted(root.rglob("*")):
        if f.is_file() and f.suffix.lower() == ".mov":
            size_mb = round(f.stat().st_size / (1024 * 1024), 1)
            rel_path = str(f.relative_to(root))
            files.append({
                "path": str(f),
                "relative_path": rel_path,
                "name": f.name,
                "size_mb": size_mb,
            })
    return files


# ======================================================================
# 文件探测
# ======================================================================


def _parse_fps(fps_str: str) -> float | None:
    """解析 ffprobe 的帧率字符串（如 '30000/1001'），返回浮点数或 None"""
    try:
        if "/" in fps_str:
            num, den = fps_str.split("/")
            return float(num) / float(den)
        return float(fps_str)
    except (ValueError, ZeroDivisionError, TypeError):
        return None


def _extract_rotation(data: dict) -> int:
    """
    从 ffprobe JSON 中提取视频旋转角度。

    检查顺序（按可靠性递减）：
      1. stream 层 tags.rotate （最常见）
      2. stream 层 side_data_list Display Matrix rotation
      3. format 层 tags.rotate （Apple QuickTime 容器级）
      4. format 层 tags.com.apple.quicktime.rotate
      5. stream 层 tags.com.apple.quicktime.display.rotation

    归一化为 0/90/180/270 后返回。
    """
    video_stream = None
    for s in data.get("streams", []):
        if s["codec_type"] == "video":
            video_stream = s
            break
    if not video_stream:
        return 0

    # 1) stream 层 tags
    tags = video_stream.get("tags", {}) or {}
    for key in ("rotate",):
        if key in tags:
            try:
                v = int(tags[key])
                if v:
                    return (v % 360 + 360) % 360
            except (ValueError, TypeError):
                pass

    # 2) stream 层 side_data Display Matrix
    for sd in video_stream.get("side_data_list", []) or []:
        if sd.get("side_data_type") == "Display Matrix":
            rot = sd.get("rotation", 0)
            if rot:
                v = int(rot)
                return (v % 360 + 360) % 360

    # 3) format 层 tags
    fmt_tags = data.get("format", {}).get("tags", {}) or {}
    for key in ("rotate", "com.apple.quicktime.rotate",
                "com.apple.quicktime.display.rotation"):
        if key in fmt_tags:
            try:
                v = int(fmt_tags[key])
                if v:
                    return (v % 360 + 360) % 360
            except (ValueError, TypeError):
                pass

    # 4) stream 层额外 Apple 命名 tag
    for key in ("com.apple.quicktime.display.rotation",):
        if key in tags:
            try:
                v = int(tags[key])
                if v:
                    return (v % 360 + 360) % 360
            except (ValueError, TypeError):
                pass

    return 0


def probe_mov_file(path: str) -> dict | None:
    """
    用 ffprobe 检测 .MOV 文件信息。

    返回:
        {
            "codec": "h264" | "hevc",
            "rotation": 0 | 90 | 180 | 270,      # 需要旋转的角度
            "is_native_portrait": bool,           # 原始尺寸已是竖屏（h > w）
            "raw_width": int,                     # 编码原始宽度
            "raw_height": int,                    # 编码原始高度
            "display_width": int,                 # 旋转后的实际显示宽度
            "display_height": int,                # 旋转后的实际显示高度
            "is_vfr": bool,                       # 是否可变帧率
            "duration": float,                    # 时长（秒）
        }
    """
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", path,
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=15)
        data = json.loads(out.stdout.decode("utf-8"))
    except Exception:
        return None

    # 找到视频流
    video_stream = None
    for s in data.get("streams", []):
        if s["codec_type"] == "video":
            video_stream = s
            break
    if not video_stream:
        return None

    codec = video_stream.get("codec_name", "").lower()

    # ---------- 旋转检测 ----------
    rotation = _extract_rotation(data)

    # ---------- 原始尺寸 ----------
    raw_w, raw_h = video_stream["width"], video_stream["height"]
    is_native_portrait = raw_h > raw_w

    # 安全网：如果原始尺寸已经是竖屏，禁止旋转（避免把已竖屏的视频转横屏）
    if is_native_portrait and rotation != 0:
        rotation = 0

    # ---------- VFR 检测 ----------
    r_fps_str = video_stream.get("r_frame_rate", "30/1")
    avg_fps_str = video_stream.get("avg_frame_rate", "30/1")
    r_fps = _parse_fps(r_fps_str)
    avg_fps = _parse_fps(avg_fps_str)

    is_vfr = False
    if avg_fps is None:
        is_vfr = True
    elif r_fps is not None and abs(avg_fps - r_fps) / max(r_fps, 1) > 0.01:
        is_vfr = True

    # ---------- 旋转后的真实显示尺寸 ----------
    if rotation in (90, 270):
        display_w, display_h = raw_h, raw_w
    else:
        display_w, display_h = raw_w, raw_h

    return {
        "codec": codec,
        "rotation": rotation,
        "is_native_portrait": is_native_portrait,
        "raw_width": raw_w,
        "raw_height": raw_h,
        "display_width": display_w,
        "display_height": display_h,
        "is_vfr": is_vfr,
        "duration": float(data.get("format", {}).get("duration", 0)),
    }


# ======================================================================
# 滤镜构建
# ======================================================================


def _build_vfilters(probe: dict) -> list[str]:
    """构建滤镜链列表"""
    filters = []

    # VFR → CFR 压制（FPS 与 pipeline 输出帧率一致）
    if probe["is_vfr"]:
        filters.append("fps=30")

    return filters


# ======================================================================
# 单文件转码
# ======================================================================


def transcode_file(input_path: str, output_path: str, callback=None):
    """
    将 .MOV 转码为适合剪辑流水线的标准 .MP4。

    策略矩阵:
    ┌────────────────────┬──────────┬───────────────────────────┐
    │ 编码               │ VFR?     │ 处理方式                  │
    ├────────────────────┼──────────┼───────────────────────────┤
    │ H.264 (AVC)        │ 否       │ -c copy 快速 remux        │
    │ H.264 (AVC)        │ 是       │ VFR→CFR + libx264 重编码  │
    │ HEVC (H.265)       │ 是/否    │ HEVC→H264 + libx264 重编码│
    └────────────────────┴──────────┴───────────────────────────┘
    注意：不做任何旋转修正，保留原始像素方向
    """
    probe = probe_mov_file(input_path)
    if not probe:
        # 降级：无法探测时走完整重编码保底
        probe = {
            "codec": "unknown",
            "rotation": 0,
            "is_native_portrait": False,
            "raw_width": 0,
            "raw_height": 0,
            "display_width": 0,
            "display_height": 0,
            "is_vfr": True,
        }

    codec = probe["codec"]
    is_vfr = probe["is_vfr"]

    # 记录探测结果（方便前端排查问题）
    probe_info = (
        f"{codec} "
        f"{probe['raw_width']}×{probe['raw_height']} "
        f"{'portrait' if probe['is_native_portrait'] else 'landscape'}"
        f"{' VFR' if is_vfr else ' CFR'}"
    )
    if callback:
        callback("log", {"message": f"  [检测] {os.path.basename(input_path)} → {probe_info}"})

    cmd = ["ffmpeg", "-y"]

    # ---------------------------------------------------------------
    # 最佳路径: H.264 + 恒定帧率 → 仅 remux，不重新编码
    # ---------------------------------------------------------------
    if codec == "h264" and not is_vfr:
        cmd += ["-i", input_path]
        cmd += ["-c:v", "copy"]
        codec_info = "H.264 remux"
    # ---------------------------------------------------------------
    # 需要重编码的路径（HEVC→H264 或 VFR→CFR）
    # ---------------------------------------------------------------
    else:
        cmd += ["-noautorotate", "-i", input_path]
        filters = _build_vfilters(probe)
        if filters:
            cmd += ["-vf", ",".join(filters)]

        # 输出为 H.264 高质量
        cmd += [
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
        ]

        # 记录处理方式供日志显示
        parts = []
        if codec == "hevc":
            parts.append("HEVC→H.264")
        elif codec == "h264":
            parts.append("H.264 re-encode")
        else:
            parts.append(f"{codec}→H.264")
        if is_vfr:
            parts.append("VFR→CFR")
        codec_info = " + ".join(parts)

    # ---------------------------------------------------------------
    # 音频：统一转 AAC
    # ---------------------------------------------------------------
    cmd += ["-c:a", "aac", "-b:a", "192k"]

    # ---------------------------------------------------------------
    # 容器优化
    # ---------------------------------------------------------------
    cmd += ["-movflags", "+faststart"]
    cmd += [output_path]

    # 执行
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=3600,
    )

    if result.returncode != 0:
        err = result.stderr[-500:] if result.stderr else "unknown error"
        raise RuntimeError(f"转码失败 ({codec_info}): {err}")

    if callback:
        callback("log", {"message": f"已完成 [{codec_info}]: {os.path.basename(output_path)}"})


# ======================================================================
# 批量转码
# ======================================================================


def batch_transcode(
    input_folder: str,
    output_folder: str,
    job_id: str,
    progress_manager,
):
    """批量转码 — 在后台线程中运行"""
    pm = progress_manager

    def callback(event_type, data):
        pm.push_event(job_id, event_type, data)

    os.makedirs(output_folder, exist_ok=True)

    try:
        pm.push_event(job_id, "log", {"message": f"正在扫描 {input_folder} ..."})
        files = scan_mov_files(input_folder)
    except Exception as e:
        pm.push_event(job_id, "error", {"message": f"扫描失败: {e}"})
        pm.push_event(job_id, "complete", {"status": "error"})
        return

    if not files:
        pm.push_event(job_id, "log", {"message": "未找到 .MOV 文件"})
        pm.push_event(job_id, "complete", {"status": "done", "total": 0, "success": 0})
        return

    total = len(files)
    pm.push_event(job_id, "log", {"message": f"找到 {total} 个 .MOV 文件，开始转码..."})
    pm.push_event(job_id, "progress", {"total": total, "done": 0, "failed": 0})

    success = 0
    failed = 0

    for i, file_info in enumerate(files, 1):
        if pm.is_cancelled(job_id):
            pm.push_event(job_id, "cancel", {"message": "用户取消"})
            return

        rel_path = file_info["relative_path"]
        rel_out = Path(rel_path).with_suffix(".mp4")
        out_path = os.path.join(output_folder, str(rel_out))
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        input_path = file_info["path"]
        pm.push_event(job_id, "log", {
            "message": f"[{i}/{total}] 转码中: {file_info['name']} ({file_info['size_mb']}MB)",
        })

        try:
            transcode_file(input_path, out_path, callback=callback)
            success += 1
        except Exception as e:
            failed += 1
            pm.push_event(job_id, "error", {
                "message": f"[{i}/{total}] 失败: {file_info['name']} — {e}",
            })

        pm.push_event(job_id, "progress", {
            "total": total,
            "done": success + failed,
            "success": success,
            "failed": failed,
            "current": rel_path,
        })

    pm.push_event(job_id, "complete", {
        "status": "done",
        "total": total,
        "success": success,
        "failed": failed,
    })

    pm.add_history({
        "type": "transcode",
        "input_folder": input_folder,
        "output_folder": output_folder,
        "total": total,
        "success": success,
        "failed": failed,
    })
