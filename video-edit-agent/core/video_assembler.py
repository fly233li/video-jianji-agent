"""视频剪辑核心模块 — 纯 ffmpeg 实现（拼接、Ken Burns、LUT、字幕、音频混合、导出）"""

import json
import os
import re
import shutil
import subprocess
import sys
import uuid

import config
from core.subtitle_gen import generate_ass


class VideoAssembler:
    """视频剪辑器 — 基于 ffmpeg filter_complex，一条命令完成全部处理"""

    def __init__(self, folder_info, progress_callback=None):
        self.folder_info = folder_info
        self.sp_map = {}
        self.progress = progress_callback or (lambda msg: None)
        self._temp_dirs = []
        self._pick_idx = {}  # 每个卖点文件夹的素材取用计数（顺序选取）

    def assemble(
        self,
        sections,
        tts_data,
        output_path,
        chosen_two=None,
        video_index=None,
        segments=None,
    ):
        """
        执行完整剪辑流程，导出单条视频（纯 ffmpeg，单次编码）。

        参数:
            sections: dict — {"开头": "...", "卖点1": "...", "卖点2": "...", "结尾": "..."}
            tts_data: dict — tts_engine.generate_tts() 的返回值
            output_path: str — 导出路径
            chosen_two: tuple(str, str) or None — 本视频选中的两个卖点
            video_index: int or None — 第几条视频（用于进度显示）
            segments: dict or None — AI 分镜结果
        """
        prefix = f"[{video_index}] " if video_index else ""

        if chosen_two:
            self.sp_map = {"卖点1": chosen_two[0], "卖点2": chosen_two[1]}

        # 创建临时工作目录
        work_dir = os.path.join(config.TEMP_DIR, f"vasm_{uuid.uuid4().hex[:8]}")
        os.makedirs(work_dir, exist_ok=True)
        self._temp_dirs.append(work_dir)

        # ----------------------------------------------------------------
        # 1. 为每个段落选取素材视频
        # ----------------------------------------------------------------
        section_order = ["开头", "卖点1", "卖点2", "结尾"]
        section_times = tts_data["section_times"]
        sec_data = []  # [(section_name, video_path_or_none, duration, ken_burns_or_none, extra_tpad, orig_duration), ...]

        self.progress(f"{prefix}正在选取素材...")
        for sec_name in section_order:
            start_t, end_t = section_times[sec_name]
            duration = end_t - start_t
            if duration <= 0:
                sec_data.append((sec_name, None, 0, None, 0, 0))
                continue

            folder_key = self.sp_map.get(sec_name, sec_name)
            paths = self._get_section_videos(folder_key)

            if not paths:
                sec_data.append((sec_name, None, duration, None, 0, 0))
                continue

            # 顺序选取素材（按文件名自然排序，逐次取用不重复）
            paths_sorted = sorted(
                paths,
                key=lambda p: [int(t) if t.isdigit() else t.lower()
                               for t in re.split(r'(\d+)', os.path.basename(p))]
            )
            idx = self._pick_idx.get(folder_key, 0)
            video_path = paths_sorted[idx % len(paths_sorted)]
            self._pick_idx[folder_key] = idx + 1
            info = self._probe_video(video_path)

            if info is None or info["duration"] <= 0:
                sec_data.append((sec_name, None, duration, None, 0, 0))
                continue

            # Ken Burns 参数
            kb = None
            if config.PAN_ENABLED:
                kb = self._gen_ken_burns(info, duration, sec_name)

            # 素材短于段落时补 tpad 克隆帧（不用 -stream_loop，避免 PTS 循环导致 concat 时序错乱）
            extra_tpad = max(0, duration - info["duration"])
            # 结尾：完整播放，不剪切
            if sec_name == "结尾":
                duration = info["duration"]
                extra_tpad = 0
            sec_data.append((sec_name, video_path, duration, kb, extra_tpad, info["duration"]))

        self.sec_data = sec_data  # 供草稿生成等下游使用

        # ----------------------------------------------------------------
        # 2. 生成 ASS 字幕文件（含入场动画）
        # ----------------------------------------------------------------
        sub_path = self._build_srt(tts_data, segments, sections, work_dir)

        # ----------------------------------------------------------------
        # 2b. LUT 文件 — 复制到临时目录避免 Windows 冒号导致的 ffmpeg 转义问题
        # ----------------------------------------------------------------
        lut_path = config.LUT_FILE if config.LUT_ENABLED and config.LUT_FILE else None
        if lut_path and os.path.exists(lut_path) and ":" in lut_path:
            import shutil
            lut_dest = os.path.join(work_dir, os.path.basename(lut_path))
            shutil.copy2(lut_path, lut_dest)
            lut_path = os.path.relpath(lut_dest).replace("\\", "/")

        # ----------------------------------------------------------------
        # 3. 构建并执行 ffmpeg 命令
        # ----------------------------------------------------------------
        self.progress(f"{prefix}正在渲染视频 (ffmpeg)...")

        total_duration = sum(d for _, _, d, _, _, _ in sec_data)
        cmd = self._build_cmd(sec_data, tts_data, sub_path, output_path, total_duration, lut_path)

        # 设置 fontconfig 路径，确保 libass 能找到 Windows 系统字体
        if getattr(sys, 'frozen', False):
            _fc_path = os.path.join(os.path.dirname(sys._MEIPASS), "fonts.conf")
        else:
            _fc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts.conf")
        _env = os.environ.copy()
        _env["FONTCONFIG_FILE"] = os.path.abspath(_fc_path)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, errors="replace",
                timeout=3600, env=_env,
            )
            if result.returncode != 0:
                err = result.stderr[-3000:] if result.stderr else "unknown error"
                filter_complex_snippet = " ".join(cmd[cmd.index("-filter_complex") + 1:cmd.index("-filter_complex") + 2]) if "-filter_complex" in cmd else ""
                raise RuntimeError(
                    f"ffmpeg 失败 (code {result.returncode})\n"
                    f"filter_complex: {filter_complex_snippet[:2000]}\n"
                    f"stderr: {err}"
                )
        except subprocess.TimeoutExpired:
            raise RuntimeError("ffmpeg 超时（>1小时）")

        self.progress(f"{prefix}导出完成 → {os.path.basename(output_path)}")

    def cleanup(self):
        """清理临时文件"""
        for d in self._temp_dirs:
            shutil.rmtree(d, ignore_errors=True)
        self._temp_dirs.clear()

    # ====================================================================
    # 内部方法
    # ====================================================================

    def _probe_video(self, path):
        """用 ffprobe 获取视频信息"""
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", path,
        ]
        try:
            out = subprocess.run(cmd, capture_output=True, timeout=15)
            data = json.loads(out.stdout.decode("utf-8"))
            video_stream = None
            for s in data.get("streams", []):
                if s["codec_type"] == "video":
                    video_stream = s
                    break
            if not video_stream:
                return None

            dur = video_stream.get("duration") or data.get("format", {}).get("duration")
            return {
                "width": video_stream["width"],
                "height": video_stream["height"],
                "duration": float(dur) if dur else 0,
                "fps": _parse_r_frame_rate(video_stream.get("r_frame_rate", "30/1")),
            }
        except Exception:
            return None

    def _get_section_videos(self, folder_key):
        """获取指定卖点/段落的素材视频列表"""
        if folder_key == "开头":
            fd = self.folder_info.get("intro_folder")
        elif folder_key == "结尾":
            fd = self.folder_info.get("outro_folder")
        else:
            fd = self.folder_info.get("folders", {}).get(folder_key)
        return fd.get("videos", []) if fd else []

    def _gen_ken_burns(self, info, target_duration, section_name=None):
        """生成 Ken Burns 参数：固定参考时长算法，保证视觉速度与素材时长无关"""
        REF_DURATION = 5.0  # 参考时长（秒），视觉速度在此时长内按 PAN_SPEED 比例移动

        src_w, src_h = info["width"], info["height"]

        # 先计算"填满画布"的最小缩放比，PAN_ZOOM 在此基础上做额外缩放
        cover_scale = max(config.OUTPUT_WIDTH / src_w, config.OUTPUT_HEIGHT / src_h)
        zoom = config.PAN_ZOOM

        scaled_w = src_w * cover_scale * zoom
        scaled_h = src_h * cover_scale * zoom

        center_x = max(0, (scaled_w - config.OUTPUT_WIDTH) / 2)
        center_y = max(0, (scaled_h - config.OUTPUT_HEIGHT) / 2)
        max_pan_x = max(0, scaled_w - config.OUTPUT_WIDTH)
        max_pan_y = max(0, scaled_h - config.OUTPUT_HEIGHT)

        # 开头：跟随运镜设置平移，但不缩放（zoom 固定为 1，只做填满画布）
        if section_name == "开头":
            mode = config.PAN_DIRECTION
            speed = config.PAN_SPEED
            top_aligned = False
            zoom = 1.0
            scaled_w = src_w * cover_scale * zoom
            scaled_h = src_h * cover_scale * zoom
            center_x = max(0, (scaled_w - config.OUTPUT_WIDTH) / 2)
            center_y = max(0, (scaled_h - config.OUTPUT_HEIGHT) / 2)
            max_pan_x = max(0, scaled_w - config.OUTPUT_WIDTH)
            max_pan_y = max(0, scaled_h - config.OUTPUT_HEIGHT)
        elif section_name == "结尾":
            mode = "zoom"
            speed = 20  # 缓慢缩放速度
            top_aligned = True
        else:
            mode = config.PAN_DIRECTION
            speed = config.PAN_SPEED
            top_aligned = False

        # 每秒移动比例 = (speed / 100) / REF_DURATION
        move_per_sec = speed / 100.0 / REF_DURATION

        # 总缩放比 = 填满画布的最小缩放 × 用户 zoom
        total_scale = cover_scale * zoom

        return {
            "mode": mode,
            "center_x": center_x,
            "center_y": center_y,
            "max_x": max_pan_x,
            "max_y": max_pan_y,
            "scale": total_scale,
            "cover_scale": cover_scale,
            "zoom": zoom,
            "fps": info["fps"],
            "move_per_sec": move_per_sec,
            "top_aligned": top_aligned,
        }

    def _build_srt(self, tts_data, segments, sections, work_dir):
        """生成 ASS 字幕文件（含入场动画）"""
        ass_path = os.path.join(work_dir, "subtitle.ass")
        generate_ass(
            tts_data["word_timestamps"],
            tts_data["section_times"],
            output_path=ass_path,
            segments=segments,
            sections=sections,
            animation=config.SUBTITLE_ANIMATION,
            animation_duration=config.SUBTITLE_ANIMATION_DURATION,
        )
        return ass_path if os.path.getsize(ass_path) > 0 else None

    def _gen_placeholder(self, duration, work_dir):
        """用 lavfi color 源生成纯色占位视频"""
        path = os.path.join(work_dir, f"ph_{uuid.uuid4().hex[:8]}.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i",
            f"color=c=0x1e1e1e:s={config.OUTPUT_WIDTH}x{config.OUTPUT_HEIGHT}:d={duration}:r={config.OUTPUT_FPS}",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            path,
        ], capture_output=True, timeout=60, check=True)
        return path

    # ====================================================================
    # ffmpeg 命令构建
    # ====================================================================

    def _build_cmd(self, sec_data, tts_data, sub_path, output_path, total_duration, lut_path=None):
        """构建单条 ffmpeg 命令"""
        cmd = ["ffmpeg", "-y"]

        # --- 输入文件 ---
        for sec_name, video_path, duration, kb, extra_tpad, orig_duration in sec_data:
            if video_path is None:
                # 生成占位视频文件
                work_dir = os.path.join(config.TEMP_DIR, f"_ph_{uuid.uuid4().hex[:8]}")
                os.makedirs(work_dir, exist_ok=True)
                self._temp_dirs.append(work_dir)
                ph = self._gen_placeholder(duration, work_dir)
                cmd.extend(["-i", ph])
            else:
                cmd.extend(["-i", video_path])

        # TTS 音频
        tts_path = tts_data["audio_path"]
        tts_idx = len(sec_data)
        cmd.extend(["-i", tts_path])

        # BGM
        bgm_path = self.folder_info.get("bgm_path")
        has_bgm = bgm_path and os.path.exists(bgm_path)
        if has_bgm:
            bgm_idx = tts_idx + 1
            cmd.extend(["-stream_loop", "-1", "-i", bgm_path])

        # --- 构建 filter_complex ---
        parts = []
        n_sec = len(sec_data)

        for i, (sec_name, video_path, duration, kb, extra_tpad, orig_duration) in enumerate(sec_data):
            if duration <= 0:
                # 零时长段落，输出一个空帧（实际不会走到这里）
                parts.append(f"[{i}:v]trim=duration=0.04,setpts=PTS-STARTPTS[s{i}]")
                continue

            chain = f"[{i}:v]"

            # LUT (使用临时拷贝路径，避免 Windows 冒号转义问题)
            if lut_path and os.path.exists(lut_path):
                lut_rel = os.path.relpath(lut_path).replace("\\", "/")
                chain += f"lut3d=file={lut_rel}:interp=tetrahedral,"

            if kb:
                # Ken Burns: 三种运镜模式（垂直向下 / 水平向右 / 中心推进）
                fps_val = kb["fps"]

                if kb["mode"] == "zoom":
                    # 缩放模式：从 cover_scale（填满画布）向总缩放比匀速推进
                    sf_expr = f"{kb['cover_scale']}+{kb['move_per_sec']}*({kb['scale']}-{kb['cover_scale']})*n/{fps_val}"
                    sf_clamp = f"if(lt({sf_expr}\\,{kb['scale']})\\,{sf_expr}\\,{kb['scale']})"
                    chain += (
                        f"scale=w=iw*{sf_clamp}:h=ih*{sf_clamp}:flags=lanczos:eval=frame,"
                    )
                    # 开口/结尾：上半部分中轴线对齐画布顶端；卖点段落：中心对齐
                    crop_y = "ih/4" if kb.get("top_aligned") else f"(ih-{config.OUTPUT_HEIGHT})/2"
                    chain += (
                        f"crop={config.OUTPUT_WIDTH}:{config.OUTPUT_HEIGHT}:"
                        f"(iw-{config.OUTPUT_WIDTH})/2:{crop_y},"
                    )
                elif kb["mode"] == "horizontal":
                    # 水平模式：匀速向右平移
                    cx_expr = f"{kb['center_x']}+{kb['move_per_sec']}*{kb['max_x']}*n/{fps_val}"
                    cx = f"min({cx_expr}\\,{kb['max_x']})"
                    chain += (
                        f"scale=w=iw*{kb['scale']}:h=ih*{kb['scale']}:flags=lanczos,"
                    )
                    chain += (
                        f"crop={config.OUTPUT_WIDTH}:{config.OUTPUT_HEIGHT}:"
                        f"{cx}:{kb['center_y']},"
                    )

                else:  # "vertical"
                    # 垂直模式：匀速向下平移
                    cy_expr = f"{kb['center_y']}+{kb['move_per_sec']}*{kb['max_y']}*n/{fps_val}"
                    cy = f"min({cy_expr}\\,{kb['max_y']})"
                    chain += (
                        f"scale=w=iw*{kb['scale']}:h=ih*{kb['scale']}:flags=lanczos,"
                    )
                    chain += (
                        f"crop={config.OUTPUT_WIDTH}:{config.OUTPUT_HEIGHT}:"
                        f"{kb['center_x']}:{cy},"
                    )
            else:
                # 无运镜：居中裁切至输出尺寸（放大填满 + 中心裁切）
                chain += (
                    f"scale=w={config.OUTPUT_WIDTH}:h={config.OUTPUT_HEIGHT}:"
                    f"force_original_aspect_ratio=2:flags=lanczos,"
                )
                chain += (
                    f"crop={config.OUTPUT_WIDTH}:{config.OUTPUT_HEIGHT},"
                )

            # 结尾：完整播放原始素材，不做剪切
            if sec_name == "结尾":
                chain += f"setpts=PTS-STARTPTS,settb=1/{config.OUTPUT_FPS},fps={config.OUTPUT_FPS}[s{i}]"
            else:
                # 从素材中间点截取，支持 xfade 过渡重叠
                xfade_extra = config.TRANSITION_DURATION if i > 0 else 0
                trim_dur = duration + xfade_extra + extra_tpad

                if video_path and orig_duration > trim_dur:
                    # 素材足够长，从中间截取
                    trim_start = (orig_duration - trim_dur) / 2
                    chain += f"trim=start={trim_start}:duration={trim_dur}"
                elif video_path:
                    # 素材不够长，取全部后补帧
                    chain += f"trim=duration={orig_duration}"
                    if xfade_extra > 0 or extra_tpad > 0:
                        chain += f",tpad=start_mode=clone:start_duration={xfade_extra}:stop_mode=clone:stop_duration={extra_tpad}"
                else:
                    # 无素材，纯占位
                    chain += f"trim=duration={trim_dur}"
                chain += f",setpts=PTS-STARTPTS,settb=1/{config.OUTPUT_FPS},fps={config.OUTPUT_FPS}[s{i}]"
            parts.append(chain)

        # xfade 交叉溶解过渡（替代 concat）
        if n_sec >= 2 and config.TRANSITION_DURATION > 0:
            td = config.TRANSITION_DURATION
            running_total = sec_data[0][2]  # 第一段时长
            prev = "[s0]"

            for i in range(1, n_sec):
                d_i = sec_data[i][2]
                label = f"v_{i}" if i < n_sec - 1 else "vid"
                parts.append(
                    f"{prev}[s{i}]xfade=transition=slideleft:duration={td}:offset={running_total - td:.4f}[{label}]"
                )
                prev = f"[{label}]"
                running_total += d_i
            video_output = "[vid]"
        elif n_sec >= 2:
            # 过渡时长为 0 时回退到 concat
            concat_in = "".join(f"[s{i}]" for i in range(n_sec))
            parts.append(f"{concat_in}concat=n={n_sec}:v=1:a=0[vid]")
            video_output = "[vid]"
        else:
            video_output = "[s0]"

        # 音频：TTS
        parts.append(
            f"[{tts_idx}:a]atrim=duration={total_duration},asetpts=PTS-STARTPTS[tts_a]"
        )

        # BGM
        if has_bgm:
            parts.append(
                f"[{bgm_idx}:a]volume={config.BGM_VOLUME},"
                f"aloop=loop=-1:size=200000,"
                f"atrim=duration={total_duration}[bgm_a]"
            )
            parts.append(
                "[tts_a][bgm_a]amix=inputs=2:duration=longest:dropout_transition=0[final_a]"
            )
            audio_map = "[final_a]"
        else:
            audio_map = "[tts_a]"

        # 字幕（用 ffmpeg 的 subtitles 滤镜烧录 ASS，含入场动画）
        if config.SUBTITLE_ENABLED and sub_path and os.path.exists(sub_path):
            sub_esc = sub_path.replace("\\", "/").replace(":", "\\:")
            parts.append(
                f"{video_output}subtitles={sub_esc}[final_v]"
            )
            video_map = "[final_v]"
        else:
            video_map = video_output

        filter_complex = ";".join(parts)
        cmd.extend(["-filter_complex", filter_complex])
        cmd.extend(["-map", video_map, "-map", audio_map])
        cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "18"])
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        cmd.extend(["-pix_fmt", "yuv420p"])
        cmd.extend(["-r", str(config.OUTPUT_FPS)])
        cmd.extend(["-y", output_path])

        return cmd


def _to_ass_color(color_str):
    """将 CSS 颜色名或十六进制转换为 ASS 格式 &H00BBGGRR"""
    if not color_str:
        return "&H00FFFFFF"
    # 已经是 ASS 格式
    if color_str.startswith("&H") or color_str.startswith("&h"):
        return color_str.upper()
    named = {
        "white": (255, 255, 255), "black": (0, 0, 0),
        "red": (255, 0, 0), "green": (0, 128, 0), "blue": (0, 0, 255),
        "yellow": (255, 255, 0), "cyan": (0, 255, 255), "magenta": (255, 0, 255),
        "gray": (128, 128, 128), "grey": (128, 128, 128),
        "orange": (255, 165, 0), "pink": (255, 192, 203), "purple": (128, 0, 128),
        "transparent": (0, 0, 0),
    }
    cs = color_str.strip().lower()
    if cs in named:
        r, g, b = named[cs]
    elif cs.startswith("#"):
        h = cs.lstrip("#")
        if len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        elif len(h) == 3:
            r, g, b = int(h[0]*2, 16), int(h[1]*2, 16), int(h[2]*2, 16)
        else:
            return "&H00FFFFFF"
    elif cs.startswith("0x"):
        h = cs[2:]
        if len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        else:
            return "&H00FFFFFF"
    else:
        return "&H00FFFFFF"
    # ASS 使用 BBGGRR 顺序
    return f"&H00{b:02X}{g:02X}{r:02X}"


def _parse_r_frame_rate(r):
    """解析 ffprobe 的 r_frame_rate 字符串（如 '30000/1001'）"""
    try:
        if "/" in r:
            num, den = r.split("/")
            return float(num) / float(den)
        return float(r)
    except (ValueError, ZeroDivisionError):
        return 30.0
