<template>
  <div>
    <PageHeader title="参数配置" description="修改视频生成参数，保存后立即生效">
      <template #extra>
        <div class="flex gap-3">
          <el-button type="primary" :loading="saving" @click="saveConfig">
            {{ saving ? '保存中...' : '保存配置' }}
          </el-button>
          <el-button :disabled="loading" @click="loadConfig">刷新</el-button>
        </div>
      </template>
    </PageHeader>

    <el-card v-if="loading" shadow="never">
      <el-skeleton :rows="6" animated />
    </el-card>

    <template v-else>
      <!-- API 配置 -->
      <el-card shadow="never" class="mb-6">
        <template #header>
          <div class="flex items-center gap-2">
            <el-icon :size="18" color="#409eff"><Setting /></el-icon>
            <span class="font-medium">API 配置</span>
          </div>
        </template>
        <el-row :gutter="24">
          <el-col :span="8">
            <el-form-item label="DeepSeek API Key">
              <el-input v-model="form.DEEPSEEK_API_KEY" type="password" show-password placeholder="sk-..." />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Base URL">
              <el-input v-model="form.DEEPSEEK_BASE_URL" placeholder="https://api.deepseek.com" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="模型">
              <el-input v-model="form.DEEPSEEK_MODEL" placeholder="deepseek-chat" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- TTS & 视频参数 -->
      <el-row :gutter="20" class="mb-6">
        <el-col :span="12">
          <el-card shadow="never" style="height: 100%">
            <template #header>
              <div class="flex items-center gap-2">
                <el-icon :size="18" color="#67c23a"><Headset /></el-icon>
                <span class="font-medium">语音配置</span>
              </div>
            </template>
            <el-form-item label="TTS 语音">
              <el-select v-model="form.TTS_VOICE" style="width: 100%">
                <el-option label="Xiaoxiao (女声)" value="zh-CN-XiaoxiaoNeural" />
                <el-option label="Yunxi (男声)" value="zh-CN-YunxiNeural" />
                <el-option label="Xiaoyi (女声)" value="zh-CN-XiaoyiNeural" />
                <el-option label="Yunjian (男声)" value="zh-CN-YunjianNeural" />
              </el-select>
            </el-form-item>
            <el-form-item label="语速">
              <el-input v-model="form.TTS_RATE" placeholder="如 +0%, +10%, -10%" />
            </el-form-item>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never" style="height: 100%">
            <template #header>
              <div class="flex items-center gap-2">
                <el-icon :size="18" color="#e6a23c"><VideoCamera /></el-icon>
                <span class="font-medium">视频参数</span>
              </div>
            </template>
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="宽度">
                  <el-input-number v-model="form.OUTPUT_WIDTH" :min="720" :max="3840" :step="2" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="高度">
                  <el-input-number v-model="form.OUTPUT_HEIGHT" :min="720" :max="3840" :step="2" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="帧率">
                  <el-input-number v-model="form.OUTPUT_FPS" :min="24" :max="60" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-card>
        </el-col>
      </el-row>

      <!-- Ken Burns + LUT -->
      <el-row :gutter="20" class="mb-6">
        <el-col :span="12">
          <el-card shadow="never" style="height: 100%">
            <template #header>
              <div class="flex items-center gap-2">
                <el-icon :size="18" color="#909399"><VideoCameraFilled /></el-icon>
                <span class="font-medium">运镜设置 (Ken Burns)</span>
                <el-switch v-model="form.PAN_ENABLED" size="small" style="margin-left: auto" />
              </div>
            </template>
            <template v-if="form.PAN_ENABLED">
              <el-form-item label="缩放系数">
                <el-slider
                  v-model="panZoomPercent"
                  :min="100" :max="200"
                  :format-tooltip="(v: number) => v + '%'"
                  style="width: 100%"
                />
              </el-form-item>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="平移方向">
                    <el-select v-model="form.PAN_DIRECTION" style="width: 100%">
                      <el-option label="垂直（向下）" value="vertical" />
                      <el-option label="水平（向右）" value="horizontal" />
                      <el-option label="缩放（推进）" value="zoom" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="移动幅度">
                    <el-slider v-model="form.PAN_SPEED" :min="1" :max="100" :format-tooltip="(v: number) => v + '%'" />
                  </el-form-item>
                </el-col>
              </el-row>
            </template>
            <div v-else class="text-center text-muted text-sm" style="padding: 20px 0">
              运镜效果已关闭，开启后可调整缩放和平移参数
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never" style="height: 100%">
            <template #header>
              <div class="flex items-center gap-2">
                <el-icon :size="18" color="#f56c6c"><MagicStick /></el-icon>
                <span class="font-medium">LUT 调色</span>
                <el-switch v-model="form.LUT_ENABLED" size="small" style="margin-left: auto" />
              </div>
            </template>
            <template v-if="form.LUT_ENABLED">
              <el-form-item label="LUT 文件">
                <el-input v-model="form.LUT_FILE" placeholder="选择 .cube 文件路径" readonly>
                  <template #append>
                    <el-button @click="pickLutFile">浏览</el-button>
                  </template>
                </el-input>
              </el-form-item>
              <p class="text-xs text-muted">使用 .cube 3D LUT 文件对视频进行调色处理</p>
            </template>
            <div v-else class="text-center text-muted text-sm" style="padding: 20px 0">
              LUT 调色已关闭，开启后可选择 .cube 文件
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 字幕样式 -->
      <el-card shadow="never" class="mb-6">
        <template #header>
          <div class="flex items-center gap-2">
            <el-icon :size="18" color="#409eff"><Document /></el-icon>
            <span class="font-medium">字幕样式</span>
            <el-switch v-model="form.SUBTITLE_ENABLED" size="small" style="margin-left: auto" />
          </div>
        </template>
        <template v-if="form.SUBTITLE_ENABLED">
          <el-row :gutter="24">
            <el-col :span="6">
              <el-form-item label="字体">
                <el-input v-model="form.SUBTITLE_FONT" placeholder="Microsoft YaHei" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="字号">
                <el-input-number v-model="form.SUBTITLE_FONT_SIZE" :min="20" :max="120" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="文字颜色">
                <el-input v-model="form.SUBTITLE_COLOR" placeholder="white" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="描边颜色">
                <el-input v-model="form.SUBTITLE_STROKE_COLOR" placeholder="black" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="24">
            <el-col :span="6">
              <el-form-item label="描边宽度">
                <el-input-number v-model="form.SUBTITLE_STROKE_WIDTH" :min="0" :max="10" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="底部边距">
                <el-input-number v-model="form.SUBTITLE_MARGIN_BOTTOM" :min="0" :max="500" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="入场动画">
                <el-select v-model="form.SUBTITLE_ANIMATION" style="width: 100%">
                  <el-option label="淡入" value="fade" />
                  <el-option label="上滑淡入" value="slide" />
                  <el-option label="无动画" value="none" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="动画时长">
                <el-input-number v-model="form.SUBTITLE_ANIMATION_DURATION" :min="100" :max="1000" :step="50" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>
        <div v-else class="text-center text-muted text-sm" style="padding: 20px 0">
          字幕已关闭，开启后可调整样式参数
        </div>
      </el-card>

      <!-- 其他 -->
      <el-card shadow="never">
        <template #header>
          <div class="flex items-center gap-2">
            <el-icon :size="18" color="#909399"><MoreFilled /></el-icon>
            <span class="font-medium">其他设置</span>
          </div>
        </template>
        <el-row :gutter="24">
          <el-col :span="8">
            <el-form-item label="BGM 音量">
              <el-slider v-model="bgmPercent" :min="0" :max="100" :format-tooltip="(v: number) => v + '%'" />
              <span class="text-xs text-muted ml-2">{{ (form.BGM_VOLUME * 100).toFixed(0) }}%</span>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="BGM 文件名">
              <el-input v-model="form.BGM_FILENAME" placeholder="bgm.mp3" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="过渡时长">
              <el-input-number v-model="form.TRANSITION_DURATION" :min="0" :max="2" :step="0.1" style="width: 100%" />
              <span class="text-xs text-muted ml-2">秒</span>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { getConfig, updateConfig, selectFile } from '../composables/useApi'
import { ElMessage } from 'element-plus'
import { Setting, Headset, VideoCamera, VideoCameraFilled, MagicStick, Document, MoreFilled } from '@element-plus/icons-vue'
import PageHeader from '../components/PageHeader.vue'

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

const bgmPercent = computed({
  get: () => Math.round(form.BGM_VOLUME * 100),
  set: (v: number) => { form.BGM_VOLUME = v / 100 },
})

const panZoomPercent = computed({
  get: () => Math.round(form.PAN_ZOOM * 100),
  set: (v: number) => { form.PAN_ZOOM = v / 100 },
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
