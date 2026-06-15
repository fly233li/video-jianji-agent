"""进度事件管理器 — 线程安全的事件队列 + 文件持久化"""

from __future__ import annotations

import json
import os
import queue as stdlib_queue
import time
import uuid
from pathlib import Path
from typing import Any

# 脚本缓存目录
_SCRIPTS_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "temp" / "scripts_cache"


def _ensure_cache_dir():
    _SCRIPTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class ProgressManager:
    """管理批量生成任务的进度事件队列"""

    def __init__(self):
        self._queues: dict[str, stdlib_queue.Queue] = {}
        self._cancelled: set[str] = set()
        self._history: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------

    def create_batch(self) -> str:
        """创建新 batch，返回 batch_id"""
        batch_id = uuid.uuid4().hex[:12]
        self._queues[batch_id] = stdlib_queue.Queue()
        return batch_id

    def get_queue(self, batch_id: str) -> stdlib_queue.Queue | None:
        return self._queues.get(batch_id)

    def remove_queue(self, batch_id: str):
        self._queues.pop(batch_id, None)
        self._cancelled.discard(batch_id)
        # 同时清理对应的脚本缓存文件（但不删除，给前端恢复留余地）
        # 文件由清理任务或下次同名 batch 写入时覆盖

    # ------------------------------------------------------------------
    # Script persistence (file-based)
    # ------------------------------------------------------------------

    def save_scripts(self, batch_id: str, scripts: list[dict[str, Any]]):
        """将文案持久化到文件 — 独立于内存队列，页面刷新后仍可恢复"""
        _ensure_cache_dir()
        path = _SCRIPTS_CACHE_DIR / f"{batch_id}.json"
        try:
            path.write_text(
                json.dumps({"batch_id": batch_id, "scripts": scripts}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass  # 写文件失败不中断用户操作

    def load_scripts(self, batch_id: str) -> list[dict[str, Any]]:
        """从文件加载已保存的文案"""
        path = _SCRIPTS_CACHE_DIR / f"{batch_id}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("scripts", [])
        except (OSError, json.JSONDecodeError):
            return []

    def has_saved_scripts(self, batch_id: str) -> bool:
        """检查 batch 是否有已保存的文案"""
        path = _SCRIPTS_CACHE_DIR / f"{batch_id}.json"
        return path.exists()

    # ------------------------------------------------------------------
    # Event push (called from background thread)
    # ------------------------------------------------------------------

    def push_event(self, batch_id: str, event_type: str, data: dict[str, Any]):
        """向指定 batch 的队列推送事件（线程安全）"""
        q = self._queues.get(batch_id)
        if q is not None:
            q.put((event_type, data))

    # ------------------------------------------------------------------
    # Cancellation
    # ------------------------------------------------------------------

    def cancel(self, batch_id: str):
        """标记 batch 为取消状态"""
        self._cancelled.add(batch_id)

    def is_cancelled(self, batch_id: str) -> bool:
        return batch_id in self._cancelled

    def clear_cancelled(self, batch_id: str):
        self._cancelled.discard(batch_id)

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def add_history(self, entry: dict[str, Any]):
        self._history.append(entry)
        # 只保留最近 20 条
        self._history[:] = self._history[-20:]

    def get_history(self, limit: int = 10) -> list[dict[str, Any]]:
        return list(self._history[-limit:])


# 全局单例
manager = ProgressManager()
