<template>
  <div>
    <PageHeader title="首页" description="钢制家具淘宝短视频批量剪辑工具" />

    <el-card shadow="never" class="mb-6">
      <template #header><span class="font-medium">快速开始</span></template>
      <el-steps :active="1" align-center>
        <el-step title="选择素材" description="指定素材文件夹和输出位置" />
        <el-step title="配置参数" description="调整视频尺寸、字幕等参数" />
        <el-step title="批量生成" description="一键生成多条视频" />
      </el-steps>
      <div class="text-center mt-4">
        <el-button type="primary" size="large" @click="$router.push('/project')">
          开始设置项目
        </el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header><span class="font-medium">最近运行记录</span></template>
      <el-timeline v-if="history.length > 0">
        <el-timeline-item
          v-for="item in history"
          :key="item.batch_id"
          :timestamp="formatTime(item.started_at)"
          :type="item.status === 'done' ? 'success' : 'danger'"
        >
          <p>生成 {{ item.total_videos }} 条视频
            <template v-if="item.success_count">（成功 {{ item.success_count }}）</template>
            <template v-if="item.fail_count">（失败 {{ item.fail_count }}）</template>
          </p>
          <p class="text-sm text-muted mt-2">耗时 {{ item.total_time }} 秒</p>
          <p class="text-sm text-muted">输出: {{ item.output_path }}</p>
        </el-timeline-item>
      </el-timeline>
      <div v-else class="empty-state">
        <el-empty description="暂无运行记录" />
        <p class="text-sm text-muted mt-3">完成一次批量生成后，运行记录将显示在这里</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getBatchHistory } from '../composables/useApi'
import PageHeader from '../components/PageHeader.vue'

const history = ref<any[]>([])

function formatTime(timestamp: number) {
  if (!timestamp) return ''
  return new Date(timestamp * 1000).toLocaleString('zh-CN')
}

onMounted(async () => {
  try {
    const res = await getBatchHistory(5)
    history.value = res.history
  } catch { /* ignore */ }
})
</script>
