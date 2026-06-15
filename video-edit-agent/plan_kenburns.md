# 9:16 竖屏素材 → 3:4 竖屏输出 + Ken Burns 运镜 实施方案

## 数学基础

| 项目 | 值 | 说明 |
|------|-----|------|
| 源素材 | 1080×1920 | 9:16 竖屏拍摄 |
| 缩放系数 | 134% (×1.34) | 用户指定，让画面填满 3:4 输出 |
| 缩放后 | 1447×2573 | 产生平移余量 |
| 输出尺寸 | 1080×1440 | 3:4 竖屏，宽高比 0.75 |
| 水平余量 | 1447−1080 = **367px** | 左右平移空间 |
| 垂直余量 | 2573−1440 = **1133px** | 上下平移空间 |

## 改动清单

### 1. config.py — 改输出尺寸 + 新增运镜参数

```
OUTPUT_WIDTH  = 1080
OUTPUT_HEIGHT = 1440              ← 从 1920 改为 1440（3:4 竖屏）

PAN_ENABLED   = True              # 是否启用平移运镜
PAN_ZOOM      = 1.34              # 缩放系数（134%）
PAN_DIRECTION = "random"          # 平移方向: horizontal/vertical/random
PAN_MARGIN    = 0.10              # 起止留边比例（不走到画面边缘）
```

### 2. video_assembler.py — 新增 Ken Burns 方法 + 替换调用

新增 `_create_ken_burns_clip(video_paths, target_duration)`：

1. 随机挑选一个素材视频，截取目标时长片段（同原逻辑）
2. 缩放至 134%（高度 ≈ 2573px）
3. 计算可平移余量：水平 367px，垂直 1133px
4. 随机起止位置（留边 10%，即不走到素材边界）
5. 自定义帧函数：每帧根据缓入缓出曲线计算 (x, y) 偏移
6. 裁切 1080×1440 窗口输出，保留原音频

`_build_video_track` 中根据 `PAN_ENABLED` 分发：

```python
if PAN_ENABLED:
    segment = self._create_ken_burns_clip(video_paths, duration)
else:
    segment = self._pick_and_trim(video_paths, duration)
```

修复 `_create_placeholder_clip` 的 `label` 参数（设为默认 None）。

### 3. subtitle_gen.py — 微调

字幕相对位置从 `0.87` → `0.85`（画面变矮，稍微上移以保持视觉舒适度）。

### 不改动的模块

- folder_reader.py, copywriter.py, tts_engine.py, main.py

## 运镜效果参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 缩放 | 134% | 填满 3:4 输出，同时产生平移余量 |
| 平移方向 | 随机水平+垂直 | 每条视频不同，避免千篇一律 |
| 起止留边 | 边缘 10% 不走到 | 画面不会露出素材边界 |
| 平移曲线 | 缓入缓出 (3t²−2t³) | 起止平滑，中间匀速 |
| 音频 | 保持原素材音频 | 不裁剪、不变速 |

## 技术实现（moviepy v2）

```python
source = VideoFileClip(path)
segment = source.subclipped(start, start + duration)
scaled = segment.resized(height=int(1920 * PAN_ZOOM))  # ≈2573px

max_pan_x = max(0, scaled.w - OUTPUT_WIDTH)   # 水平余量
max_pan_y = max(0, scaled.h - OUTPUT_HEIGHT)  # 垂直余量

margin_px_x = int(max_pan_x * PAN_MARGIN)
margin_px_y = int(max_pan_y * PAN_MARGIN)

pan_start_x = random.randint(margin_px_x, max_pan_x - margin_px_x)
pan_end_x   = random.randint(margin_px_x, max_pan_x - margin_px_x)
pan_start_y = random.randint(margin_px_y, max_pan_y - margin_px_y)
pan_end_y   = random.randint(margin_px_y, max_pan_y - margin_px_y)

def make_frame(t):
    progress = t / duration
    eased = 3 * progress**2 - 2 * progress**3  # 缓入缓出
    x = int(pan_start_x + (pan_end_x - pan_start_x) * eased)
    y = int(pan_start_y + (pan_end_y - pan_start_y) * eased)
    frame = scaled.get_frame(t)
    return frame[y:y + OUTPUT_HEIGHT, x:x + OUTPUT_WIDTH]

result = VideoClip(make_frame, duration=duration)
result = result.with_audio(segment.audio)
```

## 实施步骤

1. 修改 `config.py` 输出尺寸 + 新增参数
2. 修改 `video_assembler.py`：新增 `_create_ken_burns_clip`，按 PAN_ENABLED 分发
3. 微调 `subtitle_gen.py` 字幕位置 (0.87→0.85)
4. 测试验证
