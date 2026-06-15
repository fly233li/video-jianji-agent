import { ref } from 'vue'

/**
 * SSE 事件流封装 — 连接到后端进度事件
 */
export function useSSE() {
  let eventSource: EventSource | null = null
  const isConnected = ref(false)
  let lastKnownUrl = ''
  let savedHandlers: Record<string, (data: any) => void> = {}

  function connect(
    url: string,
    handlers: Record<string, (data: any) => void>,
  ) {
    disconnect()
    lastKnownUrl = url
    savedHandlers = { ...handlers }
    isConnected.value = false
    eventSource = new EventSource(url)

    eventSource.onopen = () => {
      console.log('[SSE] 已连接')
      isConnected.value = true
    }

    for (const [event, handler] of Object.entries(handlers)) {
      eventSource.addEventListener(event, (e: MessageEvent) => {
        try {
          handler(JSON.parse(e.data))
        } catch (err) {
          console.error(`[SSE] 解析 ${event} 事件失败:`, err)
        }
      })
    }

    eventSource.onerror = () => {
      console.log('[SSE] 连接断开或出错')
      isConnected.value = false
      // 注意: EventSource 会自动重连，不需要手动 re-create
      // 但如果是 404 等永久错误，浏览器不会重连，此时需要标记断开
      if (eventSource?.readyState === EventSource.CLOSED) {
        isConnected.value = false
      }
    }
  }

  function disconnect() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    isConnected.value = false
    lastKnownUrl = ''
    savedHandlers = {}
  }

  /**
   * 重新连接 SSE — 当连接已断开但 batch 还在时调用
   * 返回 true 表示重连成功，false 表示无法重连（无 url 记录）
   */
  async function reconnect(): Promise<boolean> {
    if (!lastKnownUrl) return false
    if (eventSource) {
      // 如果 readyState 是 CONNECTING 或 OPEN，不需要重连
      if (eventSource.readyState === EventSource.OPEN) {
        isConnected.value = true
        return true
      }
      // CLOSED 或 CONNECTING 状态：先关掉再重建
      eventSource.close()
      eventSource = null
    }
    connect(lastKnownUrl, savedHandlers)

    // 等待连接建立（最多 5 秒）
    for (let i = 0; i < 25; i++) {
      await new Promise(r => setTimeout(r, 200))
      if (eventSource?.readyState === EventSource.OPEN) {
        isConnected.value = true
        return true
      }
    }
    return false
  }

  return { connect, disconnect, reconnect, isConnected }
}
