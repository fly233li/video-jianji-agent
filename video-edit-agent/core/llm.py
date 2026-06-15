"""LLM 调用抽象层 — 支持 OpenAI / Anthropic SDK，支持 deepseek-v4-pro / deepseek-v4-flash"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class LLMBackend(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """LLM 连接配置"""
    backend: LLMBackend = LLMBackend.OPENAI
    model: str = "deepseek-v4-flash"
    api_key: str = ""
    base_url_openai: str = "https://api.deepseek.com"
    base_url_anthropic: str = "https://api.deepseek.com/anthropic"
    temperature: float = 0.3
    max_tokens: int = 500
    timeout: int = 30

    @property
    def base_url(self) -> str:
        return self.base_url_anthropic if self.backend == LLMBackend.ANTHROPIC else self.base_url_openai

    def get_defaults() -> LLMConfig:
        import config as cfg
        return LLMConfig(
            backend=LLMBackend(cfg.LLM_BACKEND),
            model=cfg.DEEPSEEK_MODEL,
            api_key=cfg.DEEPSEEK_API_KEY,
            base_url_openai=cfg.DEEPSEEK_BASE_URL,
            base_url_anthropic=cfg.DEEPSEEK_ANTHROPIC_BASE_URL,
            temperature=cfg.LLM_TEMPERATURE,
            max_tokens=cfg.LLM_MAX_TOKENS,
            timeout=cfg.LLM_TIMEOUT,
        )


# ---------------------------------------------------------------------------
# 统一的 LLM 客户端
# ---------------------------------------------------------------------------

class LLMClient:
    """封装 OpenAI / Anthropic SDK，对外提供统一的 chat() 接口"""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig.get_defaults()
        self._client = self._build_client()

    def _build_client(self):
        cfg = self.config
        if cfg.backend == LLMBackend.ANTHROPIC:
            import anthropic
            return anthropic.Anthropic(api_key=cfg.api_key, base_url=cfg.base_url)
        else:
            from openai import OpenAI
            return OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)

    def chat(
        self,
        system_prompt: str = "",
        user_prompt: str = "",
        messages: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """统一的 chat 接口 — 返回模型回复文本"""
        cfg = self.config
        temp = temperature if temperature is not None else cfg.temperature
        mt = max_tokens if max_tokens is not None else cfg.max_tokens

        if cfg.backend == LLMBackend.ANTHROPIC:
            return self._chat_anthropic(system_prompt, user_prompt, messages, temp, mt)
        else:
            return self._chat_openai(system_prompt, user_prompt, messages, temp, mt)

    # ---- OpenAI ----

    def _chat_openai(self, system_prompt, user_prompt, messages, temperature, max_tokens):
        msgs = messages or []
        if not msgs:
            if system_prompt:
                msgs.append({"role": "system", "content": system_prompt})
            msgs.append({"role": "user", "content": user_prompt})

        resp = self._client.chat.completions.create(
            model=self.config.model,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=self.config.timeout,
        )
        return resp.choices[0].message.content.strip()

    # ---- Anthropic ----

    def _chat_anthropic(self, system_prompt, user_prompt, messages, temperature, max_tokens):
        kwargs = dict(
            model=self.config.model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if system_prompt:
            kwargs["system"] = system_prompt

        if messages:
            # 用户已提供完整消息列表
            anthropic_msgs = []
            for m in messages:
                role = "assistant" if m["role"] == "assistant" else "user"
                anthropic_msgs.append({"role": role, "content": m["content"]})
            kwargs["messages"] = anthropic_msgs
        else:
            kwargs["messages"] = [{"role": "user", "content": user_prompt}]

        resp = self._client.messages.create(**kwargs)
        # content 可能包含 TextBlock / ThinkingBlock，提取文本内容
        for block in resp.content:
            if hasattr(block, "text"):
                return block.text.strip()
        return str(resp.content[0]).strip()

    # ---- 工具方法 ----

    def check_connectivity(self) -> dict:
        """测试 API 连通性和延迟"""
        if not self.config.api_key or self.config.api_key == "your-api-key-here":
            return {"status": "disconnected", "latency_ms": None, "message": "未配置 API Key"}

        try:
            start = time.time()
            self.chat(
                system_prompt="你是一个助手。",
                user_prompt="ping",
                max_tokens=1,
            )
            elapsed_ms = int((time.time() - start) * 1000)
            level = "low" if elapsed_ms < 2000 else "high"
            return {
                "status": "connected",
                "latency_ms": elapsed_ms,
                "level": level,
                "message": f"延迟 {elapsed_ms}ms",
            }
        except Exception as e:
            return {
                "status": "error",
                "latency_ms": None,
                "level": "none",
                "message": str(e),
            }
