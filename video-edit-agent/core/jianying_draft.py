"""剪映草稿生成模块 — 基于 pyJianYingDraft

为每条渲染完成的视频生成配套的 .draft 草稿，包含：
  1. 视频素材轨道 — 引用本地素材文件夹中的原始视频
  2. 配音音频轨道 — TTS 合成语音
  3. 字幕轨道 — 根据 SRT 导入的文本字幕
"""

import os

from pyJianYingDraft import (
    DraftFolder,
    VideoSegment,
    AudioSegment,
    TrackType,
    Timerange,
    SEC,
    TextStyle,
    ClipSettings,
)
from pyJianYingDraft.metadata.transition_meta import TransitionType
from pyJianYingDraft.metadata.filter_meta import FilterType

import config
from core.subtitle_gen import generate_srt


def generate_draft(
    draft_name: str,
    draft_base_dir: str,
    sec_data: list,
    tts_data: dict,
    sections: dict,
    segments: dict,
    folder_info: dict,
    output_width: int = None,
    output_height: int = None,
    fps: int = None,
):
    """为单条视频生成对应的剪映草稿（3 轨道：视频素材、配音、字幕）。

    参数:
        draft_name: 草稿名称（如 "output_001"），同时也是草稿子文件夹名
        draft_base_dir: 存放所有草稿的父目录
        sec_data: VideoAssembler 构建的段落数据
            [(sec_name, video_path, duration, kb, extra_tpad, orig_duration), ...]
        tts_data: TTS 返回数据（audio_path, section_times, word_timestamps 等）
        sections: 文案段落 {"开头": "...", "卖点1": "...", ...}
        segments: AI 分镜结果 {"开头": [...], ...}
        folder_info: scan_material_folder 的返回值
        output_width: 视频宽度（px）
        output_height: 视频高度（px）
        fps: 帧率
    """
    # ── 1. 创建草稿 ──────────────────────────────────────────────────
    output_width = output_width or config.OUTPUT_WIDTH
    output_height = output_height or config.OUTPUT_HEIGHT
    fps = fps or config.OUTPUT_FPS
    draft_folder = DraftFolder(draft_base_dir)
    script = draft_folder.create_draft(
        draft_name, output_width, output_height, fps,
        allow_replace=True,
    )

    section_times_sec = tts_data["section_times"]

    # ── 2. 视频轨道 ──────────────────────────────────────────────────
    script.add_track(TrackType.video, "视频素材")

    # 预过滤有效段落（跳过无视频或时长为零的项）
    valid_items = []
    for item in sec_data:
        sec_name, video_path, duration, *_ = item
        if video_path is None or duration <= 0:
            continue
        st = section_times_sec.get(sec_name)
        if st is None:
            continue
        valid_items.append((sec_name, video_path, duration, st))

    for i, (sec_name, video_path, duration, st) in enumerate(valid_items):
        sec_start_us = int(st[0] * SEC)
        target_dur_us = int(st[1] * SEC) - sec_start_us
        if target_dur_us <= 0:
            target_dur_us = int(duration * SEC)

        segment = VideoSegment(
            video_path,
            Timerange(sec_start_us, target_dur_us),
            speed=1.0,
        )

        # 叠化转场（除最后一段外，每段末尾添加叠化）
        if config.DRAFT_TRANSITION_ENABLED and i < len(valid_items) - 1:
            segment.add_transition(TransitionType.叠化)

        # 调色滤镜
        if config.DRAFT_COLOR_GRADING_ENABLED:
            try:
                filter_type = getattr(FilterType, config.DRAFT_COLOR_GRADING_FILTER)
                segment.add_filter(filter_type)
            except AttributeError:
                pass  # 滤镜名称无效时静默跳过

        script.add_segment(segment, "视频素材")

    # ── 3. 音频轨道（TTS 配音） ─────────────────────────────────────
    audio_path = tts_data["audio_path"]
    if os.path.exists(audio_path):
        script.add_track(TrackType.audio, "配音")
        # 用 AudioMaterial 读取精确时长
        from pyJianYingDraft.local_materials import AudioMaterial
        _mat = AudioMaterial(audio_path)
        audio_segment = AudioSegment(
            audio_path,
            Timerange(0, _mat.duration),
        )
        script.add_segment(audio_segment, "配音")

    # ── 4. 字幕轨道 ──────────────────────────────────────────────────
    srt_path = os.path.join(draft_base_dir, draft_name, "subtitles.srt")
    generate_srt(
        tts_data["word_timestamps"],
        tts_data["section_times"],
        output_path=srt_path,
        segments=segments,
        sections=sections,
    )
    if os.path.getsize(srt_path) > 0:
        text_style = TextStyle(
            size=7,
            align=1,            # 居中
            color=(1.0, 1.0, 1.0),
            auto_wrapping=True,
        )
        script.import_srt(
            srt_path,
            "字幕",
            text_style=text_style,
            clip_settings=ClipSettings(transform_y=-0.8),
        )

    # ── 5. 保存草稿 ──────────────────────────────────────────────────
    script.save()
