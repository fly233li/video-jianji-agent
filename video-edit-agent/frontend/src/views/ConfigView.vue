<template>
  <div>
    <div class="page-header">
      <h2>参数配置</h2>
      <p>修改视频生成参数，保存后立即生效</p>
    </div>

    <el-card shadow="never">
      <div class="config-actions">
        <el-button type="primary" size="default" :loading="saving" @click="saveConfig">
          保存配置
        </el-button>
        <el-button size="default" @click="loadConfig" :disabled="loading">刷新</el-button>
      </div>

      <el-collapse v-model="activePanels">
        <!-- API 配置 -->
        <el-collapse-item title="API 配置" name="api">
          <el-form label-width="160px" label-position="left">
            <el-form-item label="DeepSeek API Key">
              <el-input v-model="form.DEEPSEEK_API_KEY" type="password" show-password />
            </el-form-item>
            <el-form-item label="Base URL">
              <el-input v-model="form.DEEPSEEK_BASE_URL" />
            </el-form-item>
            <el-form-item label="模型">
              <el-input v-model="form.DEEPSEEK_MODEL" />
            </el-form-item>
          </el-form>
        </el-collapse-item>

        <!-- 语音配置 -->
        <el-collapse-item title="语音配置" name="tts">
          <el-form label-width="160px" label-position="left">
            <el-form-item label="TTS 语音">
              <el-select v-model="form.TTS_VOICE" style="width: 100%">
                <el-option label="zh-CN-XiaoxiaoNeural (女声)" value="zh-CN-XiaoxiaoNeural" />
                <el-option label="zh-CN-YunxiNeural (男声)" value="zh-CN-YunxiNeural" />
                <el-option label="zh-CN-XiaoyiNeural (女声)" value="zh-CN-XiaoyiNeural" />
                <el-option label="zh-CN-YunjianNeural (男声)" value="zh-CN-YunjianNeural" />
              </el-select>
            </el-form-item>
            <el-form-item label="语速">
              <el-input v-model="form.TTS_RATE" placeholder="如 +0%, +10%, -10%" />
            </el-form-item>
          </el-form>
        </el-collapse-item>

        <!-- 视频参数 -->
        <el-collapse-item title="视频参数" name="video">
          <el-form label-width="160px" label-position="left">
            <el-form-item label="输出宽度">
              <el-input-number v-model="form.OUTPUT_WIDTH" :min="720" :max="3840" :step="2" />
            </el-form-item>
            <el-form-item label="输出高度">
              <el-input-number v-model="form.OUTPUT_HEIGHT" :min="720" :max="3840" :step="2" />
            </el-form-item>
            <el-form-item label="帧率 (FPS)">
              <el-input-number v-model="form.OUTPUT_FPS" :min="24" :max="60" />
            </el-form-item>
          </el-form>
        </el-collapse-item>

        <!-- 运镜设置 -->
        <el-collapse-item title="运镜设置 (Ken Burns)" name="pan">
          <el-form label-width="160px" label-position="left">
            <el-form-item label="启用运镜">
              <el-switch v-model="form.PAN_ENABLED" />
            </el-form-item>
            <el-form-item label="缩放系数">
              <el-input-number v-model="form.PAN_ZOOM" :min="1.0" :max="2.0" :step="0.01" />
              <span style="margin-left: 8px; color: #909399">当前: {{ (form.PAN_ZOOM * 100).toFixed(0) }}%</span>
            </el-form-item>
            <el-form-item label="平移方向">
              <el-select v-model="form.PAN_DIRECTION" style="width: 200px">
                <el-option label="垂直（向下）" value="vertical" />
                <el-option label="水平（向右）" value="horizontal" />
                <el-option label="缩放（推进）" value="zoom" />
              </el-select>
            </el-form-item>
            <el-form-item label="移动幅度">
              <el-slider
                v-model="form.PAN_SPEED"
                :min="1"
                :max="100"
                :format-tooltip="(v: number) => v + '%'"
                style="width: 300px"
              />
              <span style="margin-left: 8px; color: #909399">
                幅度 {{ form.PAN_SPEED }}%（参考 5 秒内走完的范围比例）
              </span>
            </el-form-item>
          </el-form>
        </el-collapse-item>

        <!-- LUT 调色 -->
        <el-collapse-item title="LUT 调色" name="lut">
          <el-form label-width="160px" label-position="left">
            <el-form-item label="启用 LUT">
              <el-switch v-model="form.LUT_ENABLED" />
              <span style="margin-left: 8px; color: #909399; font-size: 12px">
                使用 .cube 3D LUT 文件对视频进行调色
              </span>
            </el-form-item>
            <el-form-item label="LUT 文件">
              <el-input v-model="form.LUT_FILE" placeholder="选择 .cube 文件路径" readonly>
                <template #append>
                  <el-button @click="pickLutFile">浏览</el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-form>
        </el-collapse-item>

        <!-- 字幕样式 -->
        <el-collapse-item title="字幕样式" name="subtitle">
          <el-form label-width="160px" label-position="left">
            <el-form-item label="显示字幕">
              <el-switch v-model="form.SUBTITLE_ENABLED" />
              <span style="margin-left: 8px; color: #909399; font-size: 12px">
                关闭后导出视频将不烧录字幕
              </span>
            </el-form-item>
            <el-form-item label="字体">
              <el-input v-model="form.SUBTITLE_FONT" placeholder="msyhbd" />
            </el-form-item>
            <el-form-item label="字号">
              <el-input-number v-model="form.SUBTITLE_FONT_SIZE" :min="20" :max="120" />
            </el-form-item>
            <el-form-item label="文字颜色">
              <el-input v-model="form.SUBTITLE_COLOR" placeholder="white" />
            </el-form-item>
            <el-form-item label="描边颜色">
              <el-input v-model="form.SUBTITLE_STROKE_COLOR" placeholder="black" />
            </el-form-item>
            <el-form-item label="描边宽度">
              <el-input-number v-model="form.SUBTITLE_STROKE_WIDTH" :min="0" :max="10" />
            </el-form-item>
            <el-form-item label="底部边距">
              <el-input-number v-model="form.SUBTITLE_MARGIN_BOTTOM" :min="0" :max="500" />
            </el-form-item>
            <el-form-item label="入场动画">
              <el-select v-model="form.SUBTITLE_ANIMATION" style="width: 200px">
                <el-option label="淡入" value="fade" />
                <el-option label="上滑淡入" value="slide" />
                <el-option label="无动画" value="none" />
              </el-select>
            </el-form-item>
            <el-form-item label="动画时长 (ms)">
              <el-input-number v-model="form.SUBTITLE_ANIMATION_DURATION" :min="100" :max="1000" :step="50" />
            </el-form-item>
          </el-form>
        </el-collapse-item>

        <!-- 其他 -->
        <el-collapse-item title="其他" name="other">
          <el-form label-width="160px" label-position="left">
            <el-form-item label="BGM 音量">
              <el-slider v-model="bgmPercent" :min="0" :max="100" :format-tooltip="(v: number) => v + '%'" />
              <span style="margin-left: 8px; color: #909399">{{ (form.BGM_VOLUME * 100).toFixed(0) }}%</span>
            </el-form-item>
            <el-form-item label="BGM 文件名">
              <el-input v-model="form.BGM_FILENAME" placeholder="bgm.mp3" />
            </el-form-item>
            <el-form-item label="过渡时长 (秒)">
              <el-input-number v-model="form.TRANSITION_DURATION" :min="0" :max="2" :step="0.1" />
            </el-form-item>
          </el-form>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { getConfig, updateConfig, selectFile } from '../composables/useApi'
import { ElMessage } from 'element-plus'

const activePanels = ref(['api', 'tts', 'video', 'pan', 'lut', 'subtitle', 'other'])
const loading = ref(true)
const saving = ref(false)

const form = reactive<Record<string, any>>({
  DEEPSEEK_API_KEY: '',
  DEEPSEEK_BASE_URL: 'https://api.deepseek.com',
  DEEPSEEK_MODEL: 'deepseek-chat',
  TTS_VOICE: 'zh-CN-XiaoxiaoNeural',
  TTS_RATE: '+0%',
  OUTPUT_WIDTH: 1080,
  OUTPUT_HEIGHT: 1440,
  OUTPUT_FPS: 30,
  PAN_ENABLED: true,
  PAN_ZOOM: 1.0,
  PAN_DIRECTION: 'vertical',
  PAN_SPEED: 10,
  BGM_VOLUME: 0.15,
  BGM_FILENAME: 'bgm.mp3',
  SUBTITLE_ENABLED: true,
  SUBTITLE_FONT_SIZE: 55,
  SUBTITLE_FONT: 'Microsoft YaHei',
  SUBTITLE_COLOR: 'white',
  SUBTITLE_STROKE_COLOR: 'black',
  SUBTITLE_STROKE_WIDTH: 3,
  SUBTITLE_MARGIN_BOTTOM: 160,
  SUBTITLE_ANIMATION: 'fade',
  SUBTITLE_ANIMATION_DURATION: 300,
  TRANSITION_DURATION: 0.3,
  LUT_ENABLED: false,
  LUT_FILE: '',
})

// Computed for sliders that need percentage display
const bgmPercent = computed({
  get: () => Math.round(form.BGM_VOLUME * 100),
  set: (v: number) => { form.BGM_VOLUME = v / 100 },
})

async function pickLutFile() {
  try {
    const res = await selectFile('请选择 LUT .cube 文件')
    if (res.path) {
      form.LUT_FILE = res.path
    }
  } catch {
    ElMessage.error('选择文件失败')
  }
}

async function loadConfig() {
  loading.value = true
  try {
    const res = await getConfig()
    Object.assign(form, res.config)
  } catch {
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  saving.value = true
  try {
    await updateConfig(form)
    ElMessage.success('配置已保存')
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '保存配置失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.config-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
</style>
