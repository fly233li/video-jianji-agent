"""素材文件夹读取模块"""

import os
from pathlib import Path

from config import SUPPORTED_VIDEO_FORMATS, BGM_FILENAME

# 不视为卖点的特殊文件夹名
EXCLUDED_FOLDERS = {"开头", "结尾"}


def scan_material_folder(folder_path):
    """
    扫描素材主文件夹，返回结构化信息。

    返回:
        dict: {
            "selling_points": ["调节脚", "挂衣杆", ...],  # 卖点名列表
            "folders": {"调节脚": ["1.mp4", ...], ...},    # 各卖点文件夹中的视频文件
            "intro_folder": str,                           # 开头文件夹路径
            "outro_folder": str,                           # 结尾文件夹路径
            "bgm_path": str or None,                       # 背景音乐路径
            "root": str,                                   # 主文件夹路径
        }
    """
    root = Path(folder_path)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"素材文件夹不存在: {folder_path}")

    result = {
        "selling_points": [],
        "folders": {},
        "intro_folder": None,
        "outro_folder": None,
        "bgm_path": None,
        "root": str(root),
    }

    # 扫描主目录下的所有子文件夹
    for item in sorted(root.iterdir()):
        if not item.is_dir():
            # 检查是否为背景音乐文件
            if item.name.lower() == BGM_FILENAME.lower() and item.is_file():
                result["bgm_path"] = str(item)
            continue

        folder_name = item.name

        # 收集该文件夹下的视频文件
        video_files = _get_video_files(item)

        if folder_name == "开头":
            result["intro_folder"] = {
                "path": str(item),
                "videos": video_files,
            }
        elif folder_name == "结尾":
            result["outro_folder"] = {
                "path": str(item),
                "videos": video_files,
            }
        elif folder_name not in EXCLUDED_FOLDERS:
            if video_files:
                result["selling_points"].append(folder_name)
                result["folders"][folder_name] = {
                    "path": str(item),
                    "videos": video_files,
                }

    # 验证必要结构
    if not result["selling_points"]:
        raise ValueError("未找到任何卖点素材文件夹（请创建以卖点命名的子文件夹）")

    if not result["intro_folder"] or not result["intro_folder"]["videos"]:
        raise ValueError("缺少「开头」素材文件夹或其内无视频文件")

    if not result["outro_folder"] or not result["outro_folder"]["videos"]:
        raise ValueError("缺少「结尾」素材文件夹或其内无视频文件")

    return result


def _get_video_files(folder_path):
    """获取文件夹中所有支持的视频文件"""
    video_files = []
    for f in sorted(folder_path.iterdir()):
        if f.is_file() and f.suffix.lower() in SUPPORTED_VIDEO_FORMATS:
            video_files.append(str(f))
    return video_files


