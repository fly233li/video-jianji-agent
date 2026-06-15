<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="app-sidebar">
      <div class="logo">
        <img src="/logo.png" class="logo-img" alt="logo">
        <span>小飞龙批量剪辑</span>
      </div>
      <el-menu
        :default-active="currentRoute"
        background-color="#eef3f7"
        text-color="#4a5a6a"
        active-text-color="#409eff"
        router
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/project">
          <el-icon><FolderOpened /></el-icon>
          <span>项目设置</span>
        </el-menu-item>
        <el-menu-item index="/config">
          <el-icon><Setting /></el-icon>
          <span>参数配置</span>
        </el-menu-item>
        <el-menu-item index="/batch">
          <el-icon><VideoPlay /></el-icon>
          <span>批量生成</span>
        </el-menu-item>
        <el-menu-item index="/transcode">
          <el-icon><Refresh /></el-icon>
          <span>视频转码</span>
        </el-menu-item>
      </el-menu>
      <div class="status-bar">
        <div class="status-item">
          <span class="status-dot" :class="llmStatusClass"></span>
          <span>大模型: {{ llmStatusText }}</span>
          <span v-if="llmLatency !== null" class="latency-text">{{ llmLatency }}ms</span>
          <el-button size="small" text type="primary" :loading="llmTesting" @click="testLLM" style="margin-left: auto">
            {{ llmTesting ? '测试中' : '测试' }}
          </el-button>
        </div>
        <div class="status-item">
          <span class="status-dot" :class="ffmpegOk ? 'online' : 'offline'"></span>
          <span>FFmpeg: {{ ffmpegOk ? '就绪' : '未找到' }}</span>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { HomeFilled, FolderOpened, Setting, VideoPlay, Refresh } from '@element-plus/icons-vue'
import { checkHealth, checkLLM } from './composables/useApi'

const route = useRoute()
const ffmpegOk = ref(false)

// LLM 连通性状态
const llmStatus = ref<'unknown' | 'connected' | 'disconnected' | 'error'>('unknown')
const llmLatency = ref<number | null>(null)
const llmTesting = ref(false)

const llmStatusClass = computed(() => {
  switch (llmStatus.value) {
    case 'connected': return llmLatency.value !== null && llmLatency.value < 2000 ? 'online' : 'warning'
    case 'disconnected': return 'offline'
    case 'error': return 'offline'
    default: return 'offline'
  }
})

const llmStatusText = computed(() => {
  switch (llmStatus.value) {
    case 'connected': return llmLatency.value !== null && llmLatency.value < 2000 ? '畅通' : '高延时'
    case 'disconnected': return '未连接'
    case 'error': return '连接失败'
    default: return '未测试'
  }
})

const currentRoute = computed(() => route.path)

async function testLLM() {
  if (llmTesting.value) return
  llmTesting.value = true
  llmStatus.value = 'unknown'
  llmLatency.value = null
  try {
    const res = await checkLLM()
    llmLatency.value = res.latency_ms
    if (res.status === 'connected') {
      llmStatus.value = 'connected'
    } else if (res.status === 'disconnected') {
      llmStatus.value = 'disconnected'
    } else {
      llmStatus.value = 'error'
    }
  } catch {
    llmStatus.value = 'error'
    llmLatency.value = null
  } finally {
    llmTesting.value = false
  }
}

onMounted(async () => {
  try {
    const health = await checkHealth()
    ffmpegOk.value = health.ffmpeg
  } catch {
    ffmpegOk.value = false
  }
})
</script>

<style scoped>
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}
.logo-img {
  height: 40px;
  width: auto;
}
</style>
