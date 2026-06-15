<template>
  <div>
    <div class="page-header">
      <h2>首页</h2>
      <p>钢制家具淘宝短视频批量剪辑工具</p>
    </div>

    <!-- 快速开始 -->
    <el-card shadow="never" style="margin-bottom: 20px">
      <template #header><span style="font-weight: 600">快速开始</span></template>
      <el-steps :active="1" align-center>
        <el-step title="选择素材" description="指定素材文件夹和输出位置" />
        <el-step title="配置参数" description="调整视频尺寸、字幕等参数" />
        <el-step title="批量生成" description="一键生成多条视频" />
      </el-steps>
      <div style="text-align: center; margin-top: 20px">
        <el-button type="primary" size="large" @click="$router.push('/project')">
          开始设置项目
        </el-button>
      </div>
    </el-card>

    <!-- 运行记录 -->
    <el-card shadow="never">
      <template #header><span style="font-weight: 600">最近运行记录</span></template>
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
          <p style="font-size: 12px; color: #909399">耗时 {{ item.total_time }} 秒</p>
          <p style="font-size: 12px; color: #909399">输出: {{ item.output_path }}</p>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无运行记录" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getBatchHistory } from '../composables/useApi'

const history = ref<any[]>([])

function formatTime(timestamp: number) {
  if (!timestamp) return ''
  const d = new Date(timestamp * 1000)
  return d.toLocaleString('zh-CN')
}

onMounted(async () => {
  try {
    const res = await getBatchHistory(5)
    history.value = res.history
  } catch {
    // ignore
  }
})
</script>
