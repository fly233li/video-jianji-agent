<template>
  <div class="log-panel-wrapper">
    <div v-if="title" class="log-panel-header">
      <span class="log-panel-title">{{ title }}</span>
      <slot name="header" />
    </div>
    <div class="log-panel" ref="containerRef">
      <div v-if="logs.length === 0" class="log-empty">暂无日志</div>
      <div
        v-for="(entry, i) in logs"
        :key="i"
        class="log-entry"
        :class="entry.type"
      >
        <span class="log-time">{{ formatTime(entry.time) }}</span>
        <span class="log-msg">{{ entry.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

export interface LogEntry {
  message: string
  type?: 'info' | 'success' | 'error' | 'warning'
  time?: Date
}

const props = withDefaults(defineProps<{
  logs: LogEntry[]
  title?: string
  maxHeight?: string
}>(), {
  maxHeight: '360px',
})

const containerRef = ref<HTMLDivElement | null>(null)

function formatTime(d?: Date) {
  if (!d) return ''
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

watch(() => props.logs.length, () => {
  nextTick(() => {
    if (containerRef.value) {
      containerRef.value.scrollTop = containerRef.value.scrollHeight
    }
  })
})
</script>

<style scoped>
.log-panel-wrapper {
  width: 100%;
}
.log-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
}
.log-panel-title {
  color: var(--color-text-secondary);
}
.log-panel {
  background: #1a1a2e;
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  max-height: v-bind(maxHeight);
  overflow-y: auto;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  line-height: 1.8;
}
.log-empty {
  color: #6b7280;
  text-align: center;
  padding: var(--space-8);
  font-family: var(--font-family);
}
</style>
