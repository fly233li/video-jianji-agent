# 小飞龙批量剪辑 — 项目状态

> 最后更新: 2026-05-14
> 下次对话请先读取本文件 + 最近的会话摘要

---

## 项目概述

淘宝钢制家具短视频批量剪辑工具。Python 后端纯 ffmpeg 处理视频，Vue 3 + Element Plus 前端 Web UI。

素材按卖点分文件夹存放 → 按顺序取用素材 (1.mp4, 2.mp4...) → 两两组合卖点 (C(9,2)=36 种) → AI 生成文案 (DeepSeek) → edge-tts 语音合成 → 视频素材拼接 (xfade slideleft 过渡 + Ken Burns 运镜 + 3D LUT + 字幕 + BGM) → 导出 3:4 竖屏 MP4。

---

## 当前架构

```
用户操作 → Vue 3 (Element Plus) → FastAPI REST API → Python 核心模块
                                      ↑ SSE 实时进度推送
                                      ↑ 生产模式同时也服务前端静态文件
```

### 运行模式

| 模式 | 启动方式 | 前端 | 后端 |
|------|----------|------|------|
| 生产模式 | `start_web.bat` | FastAPI 直接服务 `frontend/dist/` | `localhost:8000` |
| 开发模式 | `start_dev.bat` | Vite Dev Server `localhost:5175` (热更新) | `localhost:8000` |

> CLI 模式（`main.py`、`run.bat`）已移除，仅保留 Web 运行方式。

---

## 已完成功能

### 核心视频处理 (100%)

- [x] 素材文件夹扫描 — `core/folder_reader.py`
- [x] DeepSeek API 文案生成 + 模板降级 — `core/copywriter.py`
- [x] edge-tts 语音合成 + 字符级时间戳估计 — `core/tts_engine.py`
- [x] SRT 字幕生成 (heuristic + AI segmentation) — `core/subtitle_gen.py`
- [x] **纯 ffmpeg** — 单条 filter_complex 命令完成全部处理
    - scale(缩放) → crop(运镜) → trim(截取) → xfade(过渡) → amix → subtitles
- [x] 背景音乐混合 (循环/降音量)
- [x] 3:4 竖屏输出 (1080×1440)
- [x] 批量处理循环 + SSE 进度推送
- [x] xfade 幻灯片滑动过渡 (`slideleft`) — 替代 concat 硬切
- [x] 素材从中间点截取，避免头尾无用画面
- [x] 素材顺序取用（按文件名自然排序，逐次循环）

### Ken Burns 运镜 (100%)

- [x] 缩放 + 平移运镜，缩放系数可配置 (`PAN_ZOOM`)
- [x] **参考时长算法** — `REF_DURATION=5s`，保证视觉速度与素材时长无关
    - `move_per_sec = (PAN_SPEED/100) / REF_DURATION`
    - 所有时长的视频视觉移动速度完全一致
- [x] 垂直/水平/缩放三种模式
- [x] 开头/结尾段落：强制缓慢缩放 (`speed=20`) + 上半部分中轴线对齐画布顶端 (`crop_y=ih/4`)
- [x] 卖点段落：使用用户配置的运镜模式
- [x] `PAN_ENABLED` 开关

### 文案生成 (100%)

- [x] DeepSeek API 生成 + 预置模板兜底
- [x] AI 分镜切分 (按短语拆分为逐句分镜)
- [x] 开头/结尾各限 8 字以内，精简有力

### 配置系统 (100%)

- [x] `config.py` 集中管理全部参数
- [x] Web 端参数配置页面 (7 组折叠面板：API/语音/视频/运镜/LUT/字幕/其他)
- [x] 配置热重载 (`importlib.reload`) — 保存后立即生效
- [x] 字幕显示开关 (SUBTITLE_ENABLED)

### Web 前端 (100%)

- [x] FastAPI 后端 (REST API + SSE)
    - `GET /api/health` — 健康检查 + ffmpeg 状态
    - `GET/PUT /api/config` — 配置读写
    - `POST /api/project/select-folder` — tkinter 原生对话框
    - `POST /api/project/scan-folder` — 扫描素材结构
    - `POST /api/project/rename-videos` — 自动重命名素材
    - `POST /api/batch/start` — 后台启动批量生成
    - `GET /api/batch/{id}/progress` — SSE 事件流
    - `POST /api/batch/{id}/cancel` — 取消
    - `GET /api/batch/history` — 最近记录
- [x] Vue 3 + Element Plus 前端
    - 侧边栏导航 (首页/项目设置/参数配置/批量生成)
    - Logo + "小飞龙批量剪辑" 品牌标识
    - 首页仪表盘 + 运行记录时间线
    - 项目设置 (素材/输出文件夹选择 + 扫描 + 重命名)
    - 参数配置 (7 组折叠面板)
    - 批量生成 (SSE 实时进度条 + 控制台日志)
- [x] 侧边栏 LLM 连通性测试 / FFmpeg 状态检测
- [x] 生产构建 (`npm run build` → FastAPI serve static)

---

## 文件结构

```
E:\AI_jianji\video-edit-agent\
├── config.py                    # 全部可配置参数
├── logo.png                     # 品牌 Logo
├── requirements.txt             # Python 依赖
├── start_web.bat                # 生产模式一键启动
├── start_dev.bat                # 开发模式启动
├── PROJECT_STATUS.md            # 本文件
│
├── core/                        # 核心处理模块
│   ├── __init__.py
│   ├── folder_reader.py         # 素材扫描
│   ├── copywriter.py            # 文案生成 (DeepSeek + 模板)
│   ├── tts_engine.py            # 语音合成 (edge-tts)
│   ├── video_assembler.py       # 视频剪辑 (xfade + Ken Burns + LUT + 字幕)
│   └── subtitle_gen.py          # 字幕生成 + 渲染
│
├── api/                         # FastAPI 后端
│   ├── __init__.py
│   ├── app.py                   # 应用实例 + CORS + 静态文件
│   ├── schemas.py               # Pydantic 模型
│   ├── server.py                # uvicorn 入口
│   ├── folder_dialog.py         # tkinter 子进程
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── config.py            # 配置读写 (白名单 + config.py 覆写)
│   │   ├── project.py           # 项目路由 (扫描/重命名)
│   │   └── batch.py             # 批量 + SSE 路由
│   └── services/
│       ├── __init__.py
│       ├── pipeline.py          # 后台流水线
│       └── progress_manager.py  # SSE 事件队列管理
│
├── frontend/                    # Vue 3 前端
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js           # API 代理 localhost:8000, port 5175
│   ├── tsconfig.json
│   ├── dist/                    # 生产构建产物
│   ├── public/
│   │   ├── favicon.svg
│   │   ├── icons.svg
│   │   └── logo.png             # 品牌 Logo
│   └── src/
│       ├── main.ts
│       ├── App.vue              # 侧边栏布局 + Logo + 品牌名
│       ├── router/index.ts      # 4 条路由
│       ├── composables/
│       │   ├── useApi.ts        # Axios 封装
│       │   └── useSSE.ts        # EventSource 封装
│       ├── views/
│       │   ├── HomeView.vue     # 首页仪表盘
│       │   ├── ProjectView.vue  # 项目设置 (scan + rename)
│       │   ├── ConfigView.vue   # 参数配置 (7 组折叠面板)
│       │   └── BatchView.vue    # 批量生成 + SSE 实时进度
│       └── styles/global.css
│
└── temp/                        # 临时文件 (自动清理)
```

---

## 配置参考 (config.py)

| 分类 | 键 | 默认值 | 说明 |
|------|-----|--------|------|
| API | `DEEPSEEK_API_KEY` | `sk-c8c4...` | DeepSeek API Key |
| | `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | |
| | `DEEPSEEK_MODEL` | `deepseek-v4-flash` | |
| TTS | `TTS_VOICE` | `zh-CN-XiaoyiNeural` | edge-tts 语音 |
| | `TTS_RATE` | `+0%` | 语速 |
| 视频 | `OUTPUT_WIDTH` | `1080` | 输出宽度 |
| | `OUTPUT_HEIGHT` | `1440` | 输出高度 (3:4 竖屏) |
| | `OUTPUT_FPS` | `30` | |
| 运镜 | `PAN_ENABLED` | `True` | Ken Burns 开关 |
| | `PAN_ZOOM` | `1.0` | 缩放系数 |
| | `PAN_DIRECTION` | `"vertical"` | 方向: horizontal/vertical/zoom |
| | `PAN_SPEED` | `30` | 移动幅度 (参考 5s 内走完范围的比例) |
| BGM | `BGM_VOLUME` | `0.15` | 背景音乐音量 |
| | `BGM_FILENAME` | `bgm.mp3` | |
| 字幕 | `SUBTITLE_ENABLED` | `True` | 字幕显示开关 |
| | `SUBTITLE_FONT_SIZE` | `55` | 字号 |
| | `SUBTITLE_FONT` | `Microsoft YaHei` | 字体 |
| | `SUBTITLE_COLOR` | `white` | |
| | `SUBTITLE_STROKE_COLOR` | `black` | 描边颜色 |
| | `SUBTITLE_STROKE_WIDTH` | `3` | 描边宽度 |
| | `SUBTITLE_MARGIN_BOTTOM` | `160` | 底部边距 |
| LUT | `LUT_ENABLED` | `False` | 3D LUT 调色开关 |
| | `LUT_FILE` | `""` | .cube 文件路径 |
| 过渡 | `TRANSITION_DURATION` | `0.3` | xfade 过渡时长 (秒) |
| 临时 | `TEMP_DIR` | `temp` | |

---

## 关键算法

### Ken Burns 参考时长算法

`core/video_assembler.py:_gen_ken_burns()`

```
REF_DURATION = 5.0  # 固定参考时长
move_per_sec = (PAN_SPEED / 100) / REF_DURATION
# 例: PAN_SPEED=50 → move_per_sec=0.1 → 每秒走 10% 范围

# filter 表达式 (以 vertical 为例):
cy = center_y + move_per_sec * max_y * n/fps  # 与素材时长无关
capped at max_y
```

效果: 2s 素材和 10s 素材的视觉移动速度完全一致。

### 开头/结尾特殊处理

`core/video_assembler.py:_gen_ken_burns()`

- 强制 `mode="zoom"`, `speed=20` (缓慢缩放)
- `crop_y = "ih/4"` (源文件上半部分中轴线对齐画布顶端)
- 卖点段落使用用户配置的运镜模式

### xfade 过渡

`core/video_assembler.py:_build_cmd()`

- 替代 concat，每段衔接处 `slideleft` 滑动切换
- 段落 1-3 的 trim 自动追加 `TRANSITION_DURATION` 长度用作重叠
- 过渡时长为 0 时回退到 concat

### 素材顺序取用

`core/video_assembler.py:assemble()`

- 按文件名自然排序 (1.mp4 < 2.mp4 < ... < 10.mp4)
- 每个卖点维护独立计数器，逐次轮询

### 视频中间点截取

`core/video_assembler.py:_build_cmd()`

```
if orig_duration > duration:
    trim_start = (orig_duration - duration) / 2   # 从中间取
else:
    tpad 补帧
```

---

## 🔴 当前待验证/待确认

1. **[P0] xfade slideleft 效果** — 已实现但用户尚未验证效果。过渡类型在 `core/video_assembler.py:371-384`，可改 `transition=` 参数切换其他类型 (dissolve/slideleft/slideright/slideup/slidedown)。

2. **[P0] Ken Burns 视觉速度一致性** — 参考时长算法已实现，用户测试过程中发现短素材速度过快的问题已经通过 `REF_DURATION=5` 算法解决。最后一次用户测试反馈前回滚过代码，需要用户重新确认效果。

3. ~~**[P1] 配置默认值** — 当前 `DEFAULT_CONFIG` (api/routes/config.py) 与 `config.py` 实际值有差异。~~ ✅ 已修复

---

## 🔧 Python 运行时说明

WindowsApps Python 占位符 (`/c/Users/q/AppData/Local/Microsoft/WindowsApps/python`) 返回 exit code 49 无法使用。

真实 Python 路径:
```
C:\Users\q\AppData\Local\Programs\Python\Python313\python.exe
```

启动后端:
```bash
cd E:\AI_jianji\video-edit-agent
/c/Users/q/AppData/Local/Programs/Python/Python313/python.exe -m api.server
```

前端开发模式 (需要先启动后端):
```bash
cd frontend && npm run dev
```

前端生产构建:
```bash
cd frontend && npm run build
```

---

## 环境信息

| 项目 | 值 |
|------|-----|
| Python | 3.13.5 (`C:\Users\q\AppData\Local\Programs\Python\Python313\python.exe`) |
| Node.js | v24.14.0 |
| npm | 11.9.0 |
| FastAPI | installed |
| uvicorn | installed |
| edge-tts | ≥6.1.0 |
| ffmpeg | 可用 (支持 xfade + tpad) |
| 操作系统 | Windows 10 Pro |
