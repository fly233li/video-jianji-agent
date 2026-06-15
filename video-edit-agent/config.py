"""视频剪辑助手配置文件"""

# ========== DeepSeek API 配置 ==========
# LLM 后端: "openai"（默认）或 "anthropic"
LLM_BACKEND = "openai"
DEEPSEEK_API_KEY = "sk-c8c46942f9dd45219424e2270318e417"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_ANTHROPIC_BASE_URL = "https://api.deepseek.com/anthropic"
# 可用模型: deepseek-v4-pro / deepseek-v4-flash
DEEPSEEK_MODEL = "deepseek-v4-flash"
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 500
LLM_TIMEOUT = 30

# ========== 语音配置 ==========
# edge-tts 中文语音列表（可替换）：
# zh-CN-XiaoxiaoNeural (女声), zh-CN-YunxiNeural (男声)
# zh-CN-XiaoyiNeural (女声), zh-CN-YunjianNeural (男声)
TTS_VOICE = "zh-CN-XiaoxiaoNeural"
TTS_RATE = "+0%"

# ========== 视频参数 ==========
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1440
OUTPUT_FPS = 30

# ========== Ken Burns 运镜参数 ==========
PAN_ENABLED = False
PAN_ZOOM = 1
PAN_DIRECTION = "vertical"
PAN_SPEED = 10

# ========== 背景音乐 ==========
BGM_VOLUME = 0.15
BGM_FILENAME = "bgm.mp3"

# ========== 字幕样式 ==========
SUBTITLE_ENABLED = False
SUBTITLE_FONT_SIZE = 20
SUBTITLE_FONT = "TsangerYuYangT W03"
SUBTITLE_COLOR = "white"
SUBTITLE_STROKE_COLOR = "pink"
SUBTITLE_STROKE_WIDTH = 1
SUBTITLE_POSITION = ("center", "bottom")
SUBTITLE_MARGIN_BOTTOM = 50

# ========== 字幕入场动画 ==========
# none — 无动画；fade — 淡入；slide — 上滑淡入
SUBTITLE_ANIMATION = "slide"
SUBTITLE_ANIMATION_DURATION = 300

# ========== LUT 调色 ==========
LUT_ENABLED = False
LUT_FILE = ""

# ========== 视频过渡 ==========
TRANSITION_DURATION = 0.3

# ========== 临时目录 ==========
TEMP_DIR = "temp"

# ========== 支持的文件格式 ==========
SUPPORTED_VIDEO_FORMATS = (".mp4", ".mov", ".avi", ".mkv", ".webm")
