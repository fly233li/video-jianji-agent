"""Pydantic 请求/响应模型"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


# ========== Config ==========

class ConfigResponse(BaseModel):
    """完整配置快照"""
    config: dict[str, Any]
    defaults: dict[str, Any]


class ConfigUpdate(BaseModel):
    """配置更新请求 — 只传要改的字段"""
    values: dict[str, Any] = Field(..., description="要更新的配置键值对")


# ========== Project / Folder ==========

class FolderSelectRequest(BaseModel):
    title: str = "请选择文件夹"


class FolderSelectResponse(BaseModel):
    path: str | None = None


class ScanRequest(BaseModel):
    path: str


class ScanResponse(BaseModel):
    folder_info: dict[str, Any] | None = None
    error: str | None = None


class FileSelectRequest(BaseModel):
    title: str = "请选择文件"
    file_types: str = "*.cube"


class FileSelectResponse(BaseModel):
    path: str | None = None


# ========== Rename ==========

class RenameVideosRequest(BaseModel):
    folder_path: str


class RenameVideosResponse(BaseModel):
    renamed_count: int
    files: list[str]


# ========== Batch ==========

class BatchStartRequest(BaseModel):
    folder_path: str
    output_path: str
    count: int = Field(default=5, ge=1, le=500)
    product_name: str = Field(default="", description="商品名称")
    usage_scenario: str = Field(default="", description="使用场景")


class BatchStartResponse(BaseModel):
    batch_id: str
    total_videos: int
    status: str = "pending"


class BatchEntry(BaseModel):
    """单条 batch 记录"""
    batch_id: str
    status: str  # running / done / cancelled
    total_videos: int
    success_count: int = 0
    fail_count: int = 0
    total_time: float = 0.0
    started_at: float = 0.0
    output_path: str = ""
    folder_path: str = ""


class BatchHistoryResponse(BaseModel):
    history: list[BatchEntry]


class BatchStatusResponse(BaseModel):
    batch_id: str
    status: str
    progress: dict[str, Any] = Field(default_factory=dict)
    results: list[dict[str, Any]] = Field(default_factory=list)


class BatchCancelResponse(BaseModel):
    status: str = "cancelling"


# ========== Batch Preview ==========

class BatchPreviewRequest(BaseModel):
    folder_path: str
    count: int = Field(default=5, ge=1, le=500)


# ========== Script Generation (Phase 1) ==========

class ScriptItem(BaseModel):
    """单条视频的完整文案"""
    video_index: int
    selling_points: list[str]
    sections: dict[str, str]


class GenerateScriptsRequest(BaseModel):
    folder_path: str
    count: int = Field(default=5, ge=1, le=500)
    product_name: str = ""
    usage_scenario: str = ""


class GenerateScriptsResponse(BaseModel):
    batch_id: str
    total: int


# ========== Script Save/Load (实时持久化) ==========

class SaveScriptsRequest(BaseModel):
    """保存文案请求"""
    scripts: list[ScriptItem]


class ScriptsResponse(BaseModel):
    """文案加载响应"""
    scripts: list[ScriptItem]


# ========== Render (Phase 2) ==========

class StartRenderRequest(BaseModel):
    """用户确认文案后，启动 TTS + 视频渲染"""
    batch_id: str
    folder_path: str
    output_path: str
    scripts: list[ScriptItem]


class StartRenderResponse(BaseModel):
    status: str = "started"
    total: int


# ========== Regenerate Single Script ==========

class RegenerateScriptRequest(BaseModel):
    """重新生成单条文案"""
    selling_points: list[str]
    product_name: str = ""
    usage_scenario: str = ""
    video_index: int


class RegenerateScriptResponse(BaseModel):
    """单条文案重新生成结果"""
    video_index: int
    selling_points: list[str]
    sections: dict[str, str]
