<template>
  <div>
    <PageHeader
      title="视频转码"
      description="将 iPhone 拍摄的 .MOV 素材无损转码为 .MP4 格式"
    />

    <el-card shadow="never" class="mb-6">
      <el-form label-width="120px">
        <FolderPicker
          label="输入文件夹"
          v-model="inputPath"
          placeholder="请选择包含 .MOV 文件的文件夹"
          @update:model-value="onInputChange"
        />
        <FolderPicker
          label="输出文件夹"
          v-model="outputPath"
          placeholder="请选择转码后 .MP4 的输出位置"
        />
        <el-form-item>
          <el-button type="primary" :loading="scanning" :disabled="!inputPath" @click="scan">
            扫描 .MOV 文件
          </el-button>
          <el-button
            type="success"
            :loading="transcoding"
            :disabled="!canStart"
            @click="startTranscode"
            class="ml-3"
          >
            {{ transcoding ? '转码中...' : '开始转码' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Empty state -->
    <div v-if="!scanning && fileList.length === 0 && inputPath" class="empty-state mb-6">
      <el-empty description="请先扫描 .MOV 文件" />
    </div>

    <!-- File list -->
    <el-card v-if="fileList.length > 0" shadow="never" class="mb-6">
      <template #header>
        <div class="flex items-center gap-2">
          <span class="font-medium">扫描结果</span>
          <el-tag size="small" type="info">{{ fileList.length }} 个文件</el-tag>
          <el-tag v-if="progressDone > 0" size="small" type="success">{{ progressDone }} 完成</el-tag>
          <el-tag v-if="progressFailed > 0" size="small" type="danger">{{ progressFailed }} 失败</el-tag>
        </div>
      </template>
      <el-table :data="fileList" size="small" max-height="320" style="width: 100%">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="name" label="文件名" min-width="200" />
        <el-table-column prop="size_mb" label="大小" width="120" align="right">
          <template #default="{ row }">
            {{ row.size_mb }} MB
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.done" size="small" type="success">已完成</el-tag>
            <el-tag v-else-if="row.error" size="small" type="danger">失败</el-tag>
            <el-tag v-else-if="transcoding" size="small" type="warning">等待中</el-tag>
            <span v-else size="small" class="text-secondary">就绪</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Log panel -->
    <el-card v-if="logs.length > 0" shadow="never">
      <LogPanel title="转码日志" :logs="logEntries" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'
import { selectFolder, scanMovFiles, startTranscode as apiStartTranscode, getTranscodeProgressUrl } from '../composables/useApi'
import { useSSE } from '../composables/useSSE'
import { ElMessage } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import FolderPicker from '../components/FolderPicker.vue'
import LogPanel, { type LogEntry } from '../components/LogPanel.vue'

const inputPath = ref('')
const outputPath = ref('')
const fileList = ref<{ path: string; relative_path: string; name: string; size_mb: number; done?: boolean; error?: boolean }[]>([])
const scanning = ref(false)
const transcoding = ref(false)
const logs = ref<{ type: string; message: string }[]>([])
const logEntries = ref<LogEntry[]>([])
const progressTotal = ref(0)
const progressDone = ref(0)
const progressFailed = ref(0)
const jobId = ref('')

const canStart = computed(() => inputPath.value && outputPath.value && fileList.value.length > 0 && !transcoding.value)

function onInputChange() {
  fileList.value = []
  logs.value = []
  logEntries.value = []
}

async function scan() {
  if (!inputPath.value) return
  scanning.value = true
  try {
    const res = await scanMovFiles(inputPath.value)
    fileList.value = res.files.map(f => ({ ...f }))
    logs.value = []
    logEntries.value = []
    progressTotal.value = 0
    progressDone.value = 0
    progressFailed.value = 0
    if (res.total === 0) {
      ElMessage.info('未找到 .MOV 文件')
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '扫描失败')
  } finally {
    scanning.value = false
  }
}

const sse = useSSE()

function addLog(message: string, type: LogEntry['type'] = 'info') {
  logEntries.value.push({ message, type, time: new Date() })
}

async function startTranscode() {
  if (!inputPath.value || !outputPath.value) return

  fileList.value.forEach(f => { f.done = false; f.error = false })
  logs.value = []
  logEntries.value = []
  progressTotal.value = fileList.value.length
  progressDone.value = 0
  progressFailed.value = 0
  transcoding.value = true

  try {
    const res = await apiStartTranscode(inputPath.value, outputPath.value)
    jobId.value = res.job_id

    const url = getTranscodeProgressUrl(res.job_id)
    sse.connect(url, {
      log: (data: any) => {
        addLog(data.message)
      },
      progress: (data: any) => {
        progressDone.value = data.done || 0
        progressFailed.value = data.failed || 0
        progressTotal.value = data.total || 0
        if (data.current) {
          const match = fileList.value.find(f => f.relative_path === data.current)
          if (match) match.done = true
        }
      },
      error: (data: any) => {
        addLog(data.message, 'error')
        progressFailed.value++
      },
      complete: (data: any) => {
        addLog(
          data.status === 'error'
            ? '转码失败'
            : `转码完成！成功 ${data.success || 0} 个，失败 ${data.failed || 0} 个`,
          data.status === 'error' ? 'error' : 'success'
        )
        progressDone.value = data.success || 0
        progressFailed.value = data.failed || 0
        transcoding.value = false
        sse.disconnect()

        if (data.success > 0 && data.failed === 0) {
          ElMessage.success('全部转码完成')
        } else if (data.failed > 0) {
          ElMessage.warning(`完成 ${data.success || 0} 个，${data.failed} 个失败`)
        }
      },
    })
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '启动转码失败')
    transcoding.value = false
  }
}

onBeforeUnmount(() => {
  sse.disconnect()
})
</script>

<style scoped>
.ml-3 { margin-left: 12px; }
</style>
