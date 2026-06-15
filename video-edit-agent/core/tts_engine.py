"""语音合成模块 — edge-tts + 字符级时间估算"""

import asyncio
import os
import uuid
import re
import subprocess

import edge_tts

from config import TTS_VOICE, TTS_RATE, TEMP_DIR


def generate_tts(sections):
    """
    生成完整配音音频及字符级时间戳（同步接口，内部处理 asyncio）。

    edge-tts 6.x 不通过 stream() 暴露 WordBoundary 事件，
    因此采用字符均匀分布估算每句话的时间位置。

    参数:
        sections: dict — {"开头": "...", "卖点1": "...", "卖点2": "...", "结尾": "..."}

    返回:
        dict: {
            "audio_path": str,          # 合并后的完整音频路径 (.mp3)
            "word_timestamps": list,    # 每段估算的逐字时间戳 [{word, start, end}, ...]
            "section_times": dict,      # 各段落在完整音频中的起止秒数
            "total_duration": float,    # 总时长（秒）
        }
    """
    return asyncio.run(_generate_tts_async(sections))


async def _generate_tts_async(sections):
    """异步实现语音合成"""
    temp_dir = os.path.join(TEMP_DIR, f"tts_{uuid.uuid4().hex[:8]}")
    os.makedirs(temp_dir, exist_ok=True)

    section_order = ["开头", "卖点1", "卖点2", "结尾"]
    section_audio_paths = []
    section_texts = {}
    section_names_used = []

    # 第一步：逐段合成语音（分别保存以便获取每段时长）
    for section_name in section_order:
        text = sections.get(section_name, "").strip()
        if not text:
            text = "。"

        output_path = os.path.join(temp_dir, f"_{section_name}.mp3")
        await _synthesize_audio(text, output_path)

        section_audio_paths.append(output_path)
        section_texts[section_name] = text
        section_names_used.append(section_name)

    # 第二步：用 ffmpeg 合并音频并获取各段时长
    # 先通过 ffprobe 获取各段时长
    section_times = {}
    current_time = 0
    for i, section_name in enumerate(section_names_used):
        _ensure_non_empty_mp3(section_audio_paths[i])
        duration = _get_audio_duration(section_audio_paths[i])
        section_times[section_name] = [current_time, current_time + duration]
        current_time += duration

    # 用 ffmpeg concat 滤镜合并所有音频段
    final_audio_path = os.path.join(temp_dir, "final_audio.mp3")
    merge_cmd = ["ffmpeg", "-y"]
    for path in section_audio_paths:
        merge_cmd.extend(["-i", path])
    filter_ins = "".join(f"[{i}:a]" for i in range(len(section_audio_paths)))
    merge_cmd.extend([
        "-filter_complex", f"{filter_ins}concat=n={len(section_audio_paths)}:v=0:a=1[out]",
        "-map", "[out]", "-c:a", "libmp3lame", "-q:a", "2",
        final_audio_path,
    ])
    subprocess.run(merge_cmd, capture_output=True, timeout=120, check=True)

    # 第三步：按字符均匀分布生成时间戳
    all_words = []
    for section_name in section_names_used:
        text = section_texts[section_name]
        offset_start, offset_end = section_times[section_name]
        words = _estimate_word_timestamps(text, offset_start, offset_end)
        all_words.extend(words)

    total_duration = current_time

    return {
        "audio_path": final_audio_path,
        "word_timestamps": all_words,
        "section_times": section_times,
        "total_duration": total_duration,
    }


async def _synthesize_audio(text, output_path):
    """
    合成单段语音，保存为 mp3 文件。
    不依赖 WordBoundary 事件。
    """
    communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE)
    await communicate.save(output_path)


def _estimate_word_timestamps(text, offset_start, offset_end):
    """
    基于字符均匀分布估算每句话/每个字符的时间位置。

    将文本按标点符号分割为短句，每句内的字符均匀分配时间。
    """
    if not text.strip():
        return []

    duration = offset_end - offset_start
    if duration <= 0:
        duration = 1.0

    # 提取所有非空字符（包括中文汉字和英文单词）
    chars = list(text.strip())
    n_chars = len(chars)
    if n_chars == 0:
        return []

    char_duration = duration / n_chars
    words = []

    for i, ch in enumerate(chars):
        start = offset_start + i * char_duration
        end = offset_start + (i + 1) * char_duration
        words.append({
            "word": ch,
            "start": round(start, 3),
            "end": round(end, 3),
        })

    return words


def _ensure_non_empty_mp3(file_path):
    """确保 mp3 文件非空，若为空则创建最小占位文件"""
    if os.path.getsize(file_path) == 0:
        silent_path = file_path.replace(".mp3", "_silent.mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
             "-t", "0.5", "-q:a", "9", silent_path],
            capture_output=True, timeout=10,
        )
        os.replace(silent_path, file_path)


def _get_audio_duration(file_path):
    """用 ffprobe 获取音频文件时长（秒）"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", file_path],
            capture_output=True, text=True, errors="replace", timeout=15,
        )
        return float(result.stdout.strip())
    except (ValueError, subprocess.TimeoutExpired, FileNotFoundError):
        return 0.0
