# Changelog

## [v0.1.0] - 2026-06-15

### 新增
- 项目初始化，基于 FastAPI + Vue 的短视频批量剪辑工具
- 后端：文案生成（DeepSeek LLM）、TTS 语音合成（edge-tts）、视频渲染（ffmpeg）
- 前端：素材管理、批量生成、配置面板、字幕/调色/转码设置
- 剪映草稿导出：每条渲染视频自动生成配套 `.draft` 草稿

### 技术栈
- Python: FastAPI, edge-tts, pyJianYingDraft
- 前端: Vue 3, Vite, Element Plus
- 渲染: ffmpeg (Ken Burns, xfade, 字幕烧录, LUT)
