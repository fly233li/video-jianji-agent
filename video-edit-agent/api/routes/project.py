"""项目/文件夹路由 — 文件夹选择 + 扫描 + 视频重命名"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.schemas import (
    FolderSelectRequest,
    FolderSelectResponse,
    FileSelectRequest,
    FileSelectResponse,
    RenameVideosRequest,
    RenameVideosResponse,
    ScanRequest,
    ScanResponse,
)
from api.folder_dialog import show_folder_dialog, show_file_dialog
from core.folder_reader import scan_material_folder
from config import SUPPORTED_VIDEO_FORMATS

# 确保项目根目录在 sys.path 中
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

router = APIRouter(tags=["project"])


@router.post("/project/select-folder", response_model=FolderSelectResponse)
async def select_folder(body: FolderSelectRequest):
    """弹出原生文件夹选择对话框"""
    path = show_folder_dialog(title=body.title)
    return FolderSelectResponse(path=path)


@router.post("/project/select-file", response_model=FileSelectResponse)
async def select_file(body: FileSelectRequest):
    """弹出原生文件选择对话框（用于 LUT .cube 文件）"""
    path = show_file_dialog(title=body.title)
    return FileSelectResponse(path=path)


@router.post("/project/scan-folder", response_model=ScanResponse)
async def scan_folder(body: ScanRequest):
    """扫描素材文件夹结构"""
    folder_path = body.path
    if not folder_path:
        raise HTTPException(status_code=400, detail="文件夹路径不能为空")

    path_obj = Path(folder_path)
    if not path_obj.exists():
        raise HTTPException(status_code=400, detail=f"文件夹不存在: {folder_path}")
    if not path_obj.is_dir():
        raise HTTPException(status_code=400, detail=f"路径不是文件夹: {folder_path}")

    try:
        folder_info = scan_material_folder(folder_path)
        return ScanResponse(folder_info=folder_info)
    except (ValueError, FileNotFoundError) as e:
        return ScanResponse(error=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"扫描文件夹失败: {e}")


def _natural_sort_key(path: Path):
    """文件名自然排序 key（1.mp4 → 2.mp4 → 10.mp4）"""
    parts = re.split(r'(\d+)', path.stem)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


def _rename_videos_in_folder(folder: Path) -> tuple[int, list[str]]:
    """将文件夹内的视频文件按顺序重命名为 1.MP4, 2.MP4, ..."""
    video_files = sorted(
        [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_VIDEO_FORMATS],
        key=_natural_sort_key,
    )
    if not video_files:
        return 0, []

    renamed = []
    for idx, src in enumerate(video_files, start=1):
        new_name = f"{idx}.MP4"
        dst = folder / new_name
        if src == dst:
            renamed.append(str(dst))
            continue
        src.rename(dst)
        renamed.append(str(dst))

    return len(renamed), renamed


@router.post("/project/rename-videos", response_model=RenameVideosResponse)
async def rename_videos(body: RenameVideosRequest):
    """将素材主文件夹下所有子文件夹内的视频按顺序重命名为 1.MP4, 2.MP4, ..."""
    folder_path = body.folder_path
    if not folder_path:
        raise HTTPException(status_code=400, detail="文件夹路径不能为空")

    root = Path(folder_path)
    if not root.is_dir():
        raise HTTPException(status_code=400, detail=f"文件夹不存在: {folder_path}")

    try:
        total_count = 0
        all_files = []

        # 递归处理每个子文件夹
        for sub in sorted(root.iterdir()):
            if sub.is_dir():
                count, files = _rename_videos_in_folder(sub)
                total_count += count
                all_files.extend(files)

        return RenameVideosResponse(renamed_count=total_count, files=all_files)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重命名失败: {e}")
