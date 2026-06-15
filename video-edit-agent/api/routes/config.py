"""配置读写路由 — GET/PUT /api/config"""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from api.schemas import ConfigResponse, ConfigUpdate

# 确保项目根目录在 sys.path 中
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import config as cfg_module  # noqa: E402

router = APIRouter(tags=["config"])

# 已知配置键及其默认值（作为兜底）
DEFAULT_CONFIG = {
    # LLM
    "LLM_BACKEND": "openai",
    "DEEPSEEK_API_KEY": "your-api-key-here",
    "DEEPSEEK_BASE_URL": "https://api.deepseek.com",
    "DEEPSEEK_ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "DEEPSEEK_MODEL": "deepseek-v4-flash",
    "LLM_TEMPERATURE": 0.3,
    "LLM_MAX_TOKENS": 500,
    "LLM_TIMEOUT": 30,
    # TTS
    "TTS_VOICE": "zh-CN-XiaoxiaoNeural",
    "TTS_RATE": "+0%",
    # 视频
    "OUTPUT_WIDTH": 1080,
    "OUTPUT_HEIGHT": 1440,
    "OUTPUT_FPS": 30,
    # Ken Burns
    "PAN_ENABLED": True,
    "PAN_ZOOM": 1.0,
    "PAN_DIRECTION": "vertical",
    "PAN_SPEED": 10,
    # BGM
    "BGM_VOLUME": 0.15,
    "BGM_FILENAME": "bgm.mp3",
    # 字幕
    "SUBTITLE_ENABLED": False,
    "SUBTITLE_FONT_SIZE": 20,
    "SUBTITLE_FONT": "TsangerYuYangT W03",
    "SUBTITLE_COLOR": "white",
    "SUBTITLE_STROKE_COLOR": "pink",
    "SUBTITLE_STROKE_WIDTH": 1,
    "SUBTITLE_MARGIN_BOTTOM": 50,
    # 字幕入场动画
    "SUBTITLE_ANIMATION": "slide",
    "SUBTITLE_ANIMATION_DURATION": 300,
    # 过渡
    "TRANSITION_DURATION": 0.3,
    # LUT 调色
    "LUT_ENABLED": False,
    "LUT_FILE": "",
    # 临时目录
    "TEMP_DIR": "temp",
}

# 白名单：只允许这些键通过 API 修改
CONFIG_WHITELIST = set(DEFAULT_CONFIG.keys())

# ---------------------------------------------------------------------------
# 类型序列化辅助
# ---------------------------------------------------------------------------


def _format_value(value: Any) -> str:
    """将 Python 值格式化为 config.py 中的文本形式"""
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return "None"
    if isinstance(value, dict):
        items = ", ".join(f"{_format_value(k)}: {_format_value(v)}" for k, v in value.items())
        return "{" + items + "}"
    if isinstance(value, (list, tuple)):
        items = ", ".join(_format_value(v) for v in value)
        return "(" + items + ")" if isinstance(value, tuple) else "[" + items + "]"
    return repr(value)


def _read_config_module() -> dict[str, Any]:
    """读取当前 config 模块的所有值"""
    importlib.reload(cfg_module)
    result = {}
    for key in CONFIG_WHITELIST:
        if hasattr(cfg_module, key):
            result[key] = getattr(cfg_module, key)
    return result


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/config/defaults")
async def get_defaults():
    """获取默认配置"""
    return {"defaults": DEFAULT_CONFIG}


@router.get("/config")
async def get_config() -> ConfigResponse:
    """读取当前配置"""
    current = _read_config_module()
    return ConfigResponse(config=current, defaults=DEFAULT_CONFIG)


@router.put("/config")
async def update_config(body: ConfigUpdate) -> ConfigResponse:
    """更新配置（写回 config.py 并重载模块）"""
    values = body.values

    unknown = [k for k in values if k not in CONFIG_WHITELIST]
    if unknown:
        raise HTTPException(status_code=400, detail=f"未知配置键: {unknown}")

    if "DEEPSEEK_API_KEY" in values:
        key = values["DEEPSEEK_API_KEY"]
        if key and (key.startswith("http://") or key.startswith("https://") or key.startswith("/")):
            raise HTTPException(status_code=400, detail="API Key 格式无效，看起来像路径或 URL")

    try:
        _write_config_file(values)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入配置失败: {e}")

    try:
        importlib.reload(cfg_module)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重载配置失败: {e}")

    current = _read_config_module()
    return ConfigResponse(config=current, defaults=DEFAULT_CONFIG)


# ---------------------------------------------------------------------------
# 文件写入
# ---------------------------------------------------------------------------


def _write_config_file(values: dict[str, Any]) -> None:
    """原子地更新 config.py 中的指定键"""
    cfg_path = Path(cfg_module.__file__).resolve()
    content = cfg_path.read_text(encoding="utf-8")

    for key, value in values.items():
        new_line = f"{key} = {_format_value(value)}"

        old, count = _replace_config_key(content, key, new_line)
        if count == 0:
            old = content.rstrip("\n") + "\n\n" + new_line + "\n"
        content = old

    tmp = cfg_path.with_suffix(".py.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(cfg_path)


def _replace_config_key(content: str, key: str, new_line: str) -> tuple[str, int]:
    """
    在 content 中查找 KEY = ... 并替换。

    返回 (替换后的内容, 替换次数)。
    """
    lines = content.split("\n")
    new_lines = []
    replaced = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not replaced and re.match(rf"^{re.escape(key)}\s*=", stripped):
            if "{" in stripped and "}" not in stripped.split("#")[0]:
                brace_count = stripped.count("{") - stripped.count("}")
                while i < len(lines) and brace_count > 0:
                    i += 1
                    if i < len(lines):
                        brace_count += lines[i].count("{") - lines[i].count("}")
            elif "(" in stripped and ")" not in stripped.split("#")[0]:
                paren_count = stripped.count("(") - stripped.count(")")
                while i < len(lines) and paren_count > 0:
                    i += 1
                    if i < len(lines):
                        paren_count += lines[i].count("(") - lines[i].count(")")
            new_lines.append(new_line)
            replaced = True
        else:
            new_lines.append(line)
        i += 1

    return "\n".join(new_lines), (1 if replaced else 0)
