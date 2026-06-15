"""字幕生成模块 — 逐字时间戳 → SRT / ASS（含入场动画）"""

import os
import re
import uuid

from config import (
    TEMP_DIR,
    OUTPUT_WIDTH, OUTPUT_HEIGHT,
    SUBTITLE_FONT, SUBTITLE_FONT_SIZE,
    SUBTITLE_COLOR, SUBTITLE_STROKE_COLOR, SUBTITLE_STROKE_WIDTH,
    SUBTITLE_MARGIN_BOTTOM,
)


# 单行最大字符数（超过则拆分为多条连续字幕）
MAX_CHARS_PER_LINE = 18


def generate_srt(word_timestamps, section_times, output_path=None, segments=None, sections=None):
    """
    将逐字时间戳分组为字幕，生成 SRT 文件。

    参数:
        word_timestamps: list[dict] — [{word, start, end}, ...]
        section_times: dict — {"开头": [start, end], ...}
        output_path: str or None — 若为 None 则自动生成
        segments: dict or None — AI 分镜结果 {"开头": ["seg1", ...], ...}
        sections: dict or None — 原始文案 {"开头": "...", ...}

    返回:
        str: SRT 文件路径
    """
    if output_path is None:
        output_path = os.path.join(
            TEMP_DIR, f"subtitle_{uuid.uuid4().hex[:8]}.srt"
        )

    # 优先使用 AI 分镜切分，失败则回退到启发式分组
    if segments:
        subtitle_groups = _group_by_ai_segments(word_timestamps, section_times, sections, segments)
        if not subtitle_groups:
            subtitle_groups = _group_words(word_timestamps)
    else:
        subtitle_groups = _group_words(word_timestamps)

    # 将超长字幕拆分为多条，确保每条只占一行
    subtitle_groups = _split_long_groups(subtitle_groups, MAX_CHARS_PER_LINE)

    # 写入 SRT 文件
    with open(output_path, "w", encoding="utf-8") as f:
        for i, group in enumerate(subtitle_groups, 1):
            start = group["start"]
            end = group["end"]
            text = group["text"]

            # 至少保留 0.5 秒显示时间
            if end - start < 0.5:
                end = start + 0.5

            f.write(f"{i}\n")
            f.write(f"{_format_time(start)} --> {_format_time(end)}\n")
            f.write(f"{text}\n\n")

    return output_path


def _group_words(word_timestamps):
    """
    将逐字时间戳按合理语义分组为字幕。

    策略:
    - 以句号/问号/感叹号为自然断句点，每个完整句子为一条字幕
    - 逗号作为二级断句点（仅当前组超过12字时）
    - 每组最多22字，最长2.8秒
    - 相邻字间隔超过0.5秒则断开
    """
    if not word_timestamps:
        return []

    # 过滤空白字符，但保留标点以辅助断句判断
    filtered = []
    for w in word_timestamps:
        word = w["word"]
        if not word.strip():
            continue
        filtered.append(w)

    if not filtered:
        return []

    groups = []
    current_group = {"words": [], "start": None, "end": None}

    for w in filtered:
        word = w["word"]

        if current_group["start"] is None:
            current_group["start"] = w["start"]

        needs_new = False
        text_so_far = "".join(current_group["words"])

        # === 断句条件 ===

        # 1. 句尾标点（。！？）— 自然断句点，包含该标点后立即断
        if re.match(r'^[。！？]$', word) and len(text_so_far) >= 3:
            current_group["words"].append(word)
            current_group["end"] = w["end"]
            groups.append({
                "text": "".join(current_group["words"]),
                "start": current_group["start"],
                "end": current_group["end"],
            })
            current_group = {"words": [], "start": None, "end": None}
            continue

        # 2. 逗号/分号 — 当前组超过12字时断开
        if re.match(r'^[，；、：]$', word) and len(text_so_far) >= 12:
            current_group["words"].append(word)
            current_group["end"] = w["end"]
            groups.append({
                "text": "".join(current_group["words"]),
                "start": current_group["start"],
                "end": current_group["end"],
            })
            current_group = {"words": [], "start": w["start"], "end": None}
            continue

        # 3. 超过22字
        if len(text_so_far) >= 22:
            needs_new = True
        # 4. 超过2.8秒
        elif w["end"] - current_group["start"] > 2.8:
            needs_new = True
        # 5. 间隔超过0.5秒
        elif current_group["end"] is not None and w["start"] - current_group["end"] > 0.5:
            needs_new = True

        if needs_new and current_group["words"]:
            groups.append({
                "text": "".join(current_group["words"]),
                "start": current_group["start"],
                "end": current_group["end"],
            })
            current_group = {"words": [], "start": w["start"], "end": None}

        current_group["words"].append(word)
        current_group["end"] = w["end"]

    # 处理最后一组
    if current_group["words"]:
        groups.append({
            "text": "".join(current_group["words"]),
            "start": current_group["start"],
            "end": current_group["end"] or current_group["start"] + 1,
        })

    return groups


def _group_by_ai_segments(word_timestamps, section_times, sections, segments):
    """
    使用 AI 分镜结果将逐字时间戳分组为字幕。

    将 AI 定义的分句（~20 字/句）通过字符位置映射到 word_timestamps 的时间范围，
    每个分句对应一条字幕，确保断句自然、显示时长合理。
    """
    if not word_timestamps or not segments:
        return []

    section_order = ["开头", "卖点1", "卖点2", "结尾"]
    groups = []

    for section_name in section_order:
        section_segs = segments.get(section_name, [])
        section_t = section_times.get(section_name, [0, 0])
        if not section_segs:
            continue

        sec_start, sec_end = section_t

        # 获取该段落的逐字时间戳（按 start 时间严格划分段落边界，避免段落间重叠）
        sec_words = [w for w in word_timestamps
                     if sec_start <= w["start"] < sec_end]

        if not sec_words:
            continue

        # 按比例分配 — 不要求字符数精确匹配，处理AI微调标点/空格的情况
        expected_chars = sum(len(s.strip().replace(" ", ""))
                            for s in section_segs if s.strip())
        actual_chars = len(sec_words)
        ratio = actual_chars / expected_chars if expected_chars > 0 else 1.0

        if abs(expected_chars - actual_chars) > 3:
            print(f"  [WARNING]  分镜字符数差异较大 ({section_name}): "
                  f"期望 {expected_chars}, 实际 {actual_chars}，尝试按比例分配")
            # 差异过大时仍尝试，但用比例调整分配

        # 按字符位置将 sec_words 分配给每个分句
        char_idx = 0
        for seg_text in section_segs:
            seg_clean = seg_text.strip()
            if not seg_clean:
                continue
            if re.match(r'^[，。！？、；：…—\xb7\s]$', seg_clean):
                continue

            # 按比例调整每个分句的预期字数
            seg_len = max(1, int(len(seg_clean) * ratio))
            seg_ts = sec_words[char_idx:char_idx + seg_len]
            char_idx += seg_len

            if not seg_ts:
                continue

            seg_start = seg_ts[0]["start"]
            seg_end = seg_ts[-1]["end"]
            if seg_end - seg_start < 0.5:
                seg_end = seg_start + 0.5

            groups.append({
                "text": seg_clean,
                "start": seg_start,
                "end": seg_end,
            })

    return groups


def _split_long_groups(groups, max_chars=18):
    """
    将文本过长的字幕拆分为多条连续字幕，确保每条只占一行。

    通过字符比例将原时间均分给拆分后的每条字幕。
    """
    result = []
    for group in groups:
        text = group["text"]
        start = group["start"]
        end = group["end"]
        duration = end - start

        if len(text) <= max_chars or duration <= 0:
            result.append(group)
            continue

        # 按 max_chars 切分文本
        chunks = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]

        # 按字符比例分配时间
        total_chars = len(text)
        char_duration = duration / total_chars

        chunk_start = start
        for chunk in chunks:
            chunk_dur = len(chunk) * char_duration
            chunk_end = chunk_start + chunk_dur
            # 至少 0.5 秒，但不超过原始结束时间
            if chunk_end - chunk_start < 0.5:
                chunk_end = min(chunk_start + 0.5, end)
            # 不超过原始结束时间
            if chunk_end > end:
                chunk_end = end
            result.append({
                "text": chunk,
                "start": chunk_start,
                "end": chunk_end,
            })
            if chunk_end >= end:
                break
            chunk_start = chunk_end

    return result


def _format_time(seconds):
    """将秒数转换为 SRT 时间格式 HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")


# ====================================================================
# ASS 字幕 — 支持入场动画
# ====================================================================

def _css_color_to_ass(color_str):
    """将 CSS 颜色名或 #RRGGBB 转换为 ASS 格式 &H00BBGGRR"""
    if not color_str:
        return "FFFFFF"
    color_str = color_str.strip()
    if color_str.startswith("&H") or color_str.startswith("&h"):
        return color_str[3:].upper()
    named = {
        "white": (255, 255, 255), "black": (0, 0, 0),
        "red": (255, 0, 0), "green": (0, 128, 0), "blue": (0, 0, 255),
        "yellow": (255, 255, 0), "cyan": (0, 255, 255), "magenta": (255, 0, 255),
        "gray": (128, 128, 128), "grey": (128, 128, 128),
        "pink": (255, 192, 203), "orange": (255, 165, 0), "purple": (128, 0, 128),
    }
    rgb = named.get(color_str.lower())
    if rgb:
        r, g, b = rgb
    elif color_str.startswith("#") and len(color_str) == 7:
        r, g, b = int(color_str[1:3], 16), int(color_str[3:5], 16), int(color_str[5:7], 16)
    else:
        r, g, b = 255, 255, 255
    return f"{b:02X}{g:02X}{r:02X}"


def _format_ass_time(seconds):
    """将秒数转换为 ASS 时间格式 H:MM:SS.cc"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"


def generate_ass(word_timestamps, section_times, output_path=None,
                 segments=None, sections=None,
                 animation="fade", animation_duration=300):
    """
    将逐字时间戳分组为字幕，生成 ASS 文件（含入场动画）。

    参数:
        word_timestamps: list[dict] — [{word, start, end}, ...]
        section_times: dict — {"开头": [start, end], ...}
        output_path: str or None — 若为 None 则自动生成
        segments: dict or None — AI 分镜结果
        sections: dict or None — 原始文案
        animation: str — "fade", "slide", "none"
        animation_duration: int — 动画时长（毫秒）

    返回:
        str: ASS 文件路径
    """
    import config  # 实时读取，支持 API 热重载

    if output_path is None:
        output_path = os.path.join(
            TEMP_DIR, f"subtitle_{uuid.uuid4().hex[:8]}.ass"
        )

    # 分组逻辑复用 SRT 的相同算法
    if segments:
        subtitle_groups = _group_by_ai_segments(word_timestamps, section_times, sections, segments)
        if not subtitle_groups:
            subtitle_groups = _group_words(word_timestamps)
    else:
        subtitle_groups = _group_words(word_timestamps)

    subtitle_groups = _split_long_groups(subtitle_groups, MAX_CHARS_PER_LINE)

    # 颜色值
    primary = _css_color_to_ass(config.SUBTITLE_COLOR)
    outline = _css_color_to_ass(config.SUBTITLE_STROKE_COLOR)

    # 标准 ASS PlayRes — 使用 libass 默认值 384×288
    # 注意：config 中的字幕数值（字号/边距/描边）本身就是按 PlayResY=288 坐标空间设计的，
    # 因为 ffmpeg 内部 SRT→ASS 转换也使用同样的 PlayRes，所以直接使用，无需额外缩放。
    ass_playres_x = 384
    ass_playres_y = 288
    font_size = max(1, int(config.SUBTITLE_FONT_SIZE))
    margin_v = max(0, int(config.SUBTITLE_MARGIN_BOTTOM))
    stroke_width = max(0, int(config.SUBTITLE_STROKE_WIDTH))

    # 生成 ASS 内容
    lines = []
    lines.append("[Script Info]")
    lines.append("ScriptType: v4.00+")
    lines.append(f"PlayResX: {ass_playres_x}")
    lines.append(f"PlayResY: {ass_playres_y}")
    lines.append("ScaledBorderAndShadow: yes")
    lines.append("")

    lines.append("[V4+ Styles]")
    lines.append(
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding"
    )
    lines.append(
        f"Style: Default,{config.SUBTITLE_FONT},{font_size},"
        f"&H00{primary},&H000000FF,&H00{outline},&H00000000,"
        f"0,0,0,0,100,100,0,0,1,{stroke_width},0,"
        f"2,10,10,{margin_v},1"
    )
    lines.append("")

    lines.append("[Events]")
    lines.append(
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    )

    # 入场动画标签
    if animation == "fade":
        anim_tag = f"{{\\fad({animation_duration},{animation_duration // 2})}}"
    elif animation == "slide":
        anim_tag = f"{{\\fad({animation_duration},{animation_duration // 2})}}"
    else:  # none
        anim_tag = ""

    for group in subtitle_groups:
        start_s = group["start"]
        end_s = group["end"]
        text = group["text"]

        # 字幕至少显示 animation_duration*2 毫秒，确保动画完成后有可见时间
        min_duration = max(0.5, animation_duration * 2 / 1000)
        if end_s - start_s < min_duration:
            end_s = start_s + min_duration

        lines.append(
            f"Dialogue: 0,{_format_ass_time(start_s)},{_format_ass_time(end_s)},"
            f"Default,,0,0,0,,{anim_tag}{text}"
        )

    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path
