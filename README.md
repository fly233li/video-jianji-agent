<p align="center">
  <img src="video-edit-agent/logo.png" alt="logo" width="120"/>
</p>

<h1 align="center">Video Edit Agent</h1>

<p align="center">
  <b>短视频批量剪辑自动化工具</b><br>
  文案生成 · TTS 语音合成 · 视频渲染 · 剪映草稿导出
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.109+-green" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue_3-3.4+-brightgreen" alt="Vue3">
  <img src="https://img.shields.io/badge/license-Apache--2.0-red" alt="License">
  <img src="https://img.shields.io/github/v/release/fly233li/video-jianji-agent" alt="Version">
</p>

---

## 概述

**Video Edit Agent** 是一个面向电商带货场景的**短视频批量剪辑自动化工具**。它能够：

1. 根据商品卖点自动生成叫卖风格的短视频文案
2. 通过 AI 对文案进行分镜切分
3. 合成自然语音配音（边缘 TTS）
4. 使用 ffmpeg 将素材视频、配音和字幕合成为成品视频
5. 自动生成配套的 **剪映（CapCut）草稿**，方便二次精修

整个流程从素材到成品全自动，适合批量化生产短视频内容。

---

## 功能特性

### 📝 文案生成
- 接入 **DeepSeek / OpenAI / Anthropic** 大语言模型
- 自动按"开头-卖点1-卖点2-结尾"四段式结构生成文案
- 卖点两两组合，批量生成多条差异化文案
- API 失败时自动降级到预置模板兜底
- AI 分镜切分，按短语粒度断句

### 🎤 语音合成
- 基于 **edge-tts** 的高质量中文语音
- 支持多种声线（女声/男声）
- 字符级时间戳估算，精确对齐字幕

### 🎬 视频渲染
- 纯 **ffmpeg** 渲染，单条命令完成全部处理
- 多段落 xfade 交叉溶解过渡
- Ken Burns 运镜效果（缩放/平移）
- ASS 字幕烧录（支持淡入/上滑动画）
- LUT 调色
- BGM 背景音乐混音

### 📐 剪映草稿导出
- 每条成品视频自动生成配套 **剪映草稿**
- 三轨道结构：**视频素材 → 配音音频 → 字幕**
- 视频素材引用本地原始文件绝对路径
- 草稿可在剪映中直接打开进行精修

### 🖥️ 可视化管理面板
- 基于 **Vue 3 + Element Plus** 的 Web 管理界面
- 实时 SSE 进度推送
- 文案在线编辑/审核
- 批量渲染状态追踪

---

## 快速开始

### 环境要求

| 依赖 | 版本 |
|------|------|
| Python | 3.8+ |
| ffmpeg | 可用（需在 PATH 中） |
| Node.js | 18+（仅前端开发需要） |

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/fly233li/video-jianji-agent.git
cd video-jianji-agent/video-edit-agent

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. （可选）安装前端依赖，用于前端开发
cd frontend
npm install
cd ..

# 4. 配置 API Key
# 编辑 config.py，设置 DEEPSEEK_API_KEY（或 LLM 后端配置）
```

### 启动

```bash
# 启动后端服务
python -m api.server

# 服务运行在 http://127.0.0.1:8000
```

### 素材文件夹结构

素材目录需按以下结构组织，每个卖点对应一个子文件夹：

```
素材根目录/
├── 开头/              # 开头视频素材
│   ├── 1.mp4
│   └── 2.mp4
├── 卖点A/             # 卖点 A 素材
│   └── 1.mp4
├── 卖点B/             # 卖点 B 素材
│   └── 1.mp4
├── 结尾/              # 结尾视频素材
│   └── 1.mp4
└── bgm.mp3            # （可选）背景音乐
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python) |
| 前端框架 | Vue 3 + Vite + Element Plus |
| LLM 接入 | OpenAI SDK / Anthropic SDK |
| 语音合成 | edge-tts |
| 视频渲染 | ffmpeg (filter_complex) |
| 剪映草稿 | pyJianYingDraft |
| 桌面打包 | PyInstaller + Electron |

---

## 项目结构

```
E:\AI_jianji/
├── video-edit-agent/          # 主项目目录
│   ├── api/                   # FastAPI 后端
│   │   ├── app.py             # 应用入口
│   │   ├── server.py          # 启动脚本
│   │   ├── schemas.py         # Pydantic 模型
│   │   ├── routes/            # API 路由
│   │   │   ├── batch.py       # 批量生成/渲染
│   │   │   ├── config.py      # 配置管理
│   │   │   ├── project.py     # 素材管理
│   │   │   └── transcode.py   # 转码
│   │   └── services/
│   │       ├── pipeline.py    # 批处理流水线
│   │       └── progress_manager.py  # SSE 进度管理
│   ├── core/                  # 核心功能
│   │   ├── copywriter.py      # 文案生成
│   │   ├── tts_engine.py      # 语音合成
│   │   ├── video_assembler.py # 视频组装
│   │   ├── subtitle_gen.py    # 字幕生成
│   │   ├── jianying_draft.py  # 剪映草稿导出
│   │   ├── transcoder.py      # 转码工具
│   │   ├── folder_reader.py   # 素材扫描
│   │   └── llm.py             # LLM 客户端
│   ├── frontend/              # Vue3 前端
│   ├── config.py              # 项目配置
│   └── requirements.txt       # Python 依赖
├── CHANGELOG.md               # 版本更新记录
└── README.md                  # 本文件
```

---

## 使用流程

```mermaid
graph LR
    A[准备素材] --> B[启动服务]
    B --> C[选择素材目录]
    C --> D[生成文案]
    D --> E[审核/编辑文案]
    E --> F[批量渲染]
    F --> G[成品 MP4 + 剪映草稿]
```

### 详细步骤

1. **准备素材** — 按上述文件夹结构存放视频素材
2. **启动服务** — 运行 `python -m api.server`，打开 `http://localhost:8000`
3. **选择素材目录** — 在"项目管理"页选择素材根目录
4. **生成文案** — 设置生成数量，点击"批量生成"
5. **审核文案** — 在线编辑不满意的文案，可单条重新生成
6. **渲染视频** — 确认文案后启动渲染，实时查看进度
7. **获取成品** — 渲染完成后在输出目录获取 MP4 及配套剪映草稿

### 剪映草稿

每条视频渲染完成后，在输出目录的 `drafts/` 子目录下生成对应的剪映草稿：

```
输出目录/
├── output_001.mp4
├── output_002.mp4
└── drafts/
    ├── output_001/
    │   ├── draft_content.json   ← 剪映草稿
    │   ├── draft_meta_info.json
    │   └── subtitles.srt
    └── output_002/              ← 每条视频对应一个草稿
        └── ...
```

在剪映中点击 **导入草稿** → 选择草稿文件夹即可打开精修。

---

## 配置说明

主要配置项位于 `video-edit-agent/config.py`：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | LLM API Key | - |
| `TTS_VOICE` | 语音声线 | zh-CN-XiaoxiaoNeural |
| `OUTPUT_WIDTH/HEIGHT` | 输出分辨率 | 1080×1440 |
| `PAN_ENABLED` | Ken Burns 运镜 | False |
| `SUBTITLE_ENABLED` | 字幕开关 | False |
| `LUT_ENABLED` | LUT 调色开关 | False |
| `TRANSITION_DURATION` | 段落过渡时长 | 0.3s |

---

## 版本记录

详见 [CHANGELOG.md](CHANGELOG.md)

## 许可

本项目基于 [Apache-2.0](LICENSE) 许可证。
