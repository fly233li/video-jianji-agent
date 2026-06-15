import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { checkHealth, checkLLM } from '../composables/useApi'

export const useAppStore = defineStore('app', () => {
  const ffmpegOk = ref(false)
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

  async function testLLM() {
    if (llmTesting.value) return
    llmTesting.value = true
    llmStatus.value = 'unknown'
    llmLatency.value = null
    try {
      const res = await checkLLM()
      llmLatency.value = res.latency_ms
      llmStatus.value = res.status === 'connected' ? 'connected'
        : res.status === 'disconnected' ? 'disconnected' : 'error'
    } catch {
      llmStatus.value = 'error'
      llmLatency.value = null
    } finally {
      llmTesting.value = false
    }
  }

  async function checkServerHealth() {
    try {
      const health = await checkHealth()
      ffmpegOk.value = health.ffmpeg
    } catch {
      ffmpegOk.value = false
    }
  }

  return {
    ffmpegOk, llmStatus, llmLatency, llmTesting,
    llmStatusClass, llmStatusText,
    testLLM, checkServerHealth,
  }
})
