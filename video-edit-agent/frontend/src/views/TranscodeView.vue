<template>
  <div>
    <div class="page-header">
      <h2>视频转码</h2>
      <p>将 iPhone 拍摄的 .MOV 素材无损转码为 .MP4 格式</p>
    </div>

    <el-card shadow="never" style="margin-bottom: 20px">
      <el-form label-width="120px">
        <el-form-item label="输入文件夹">
          <el-input v-model="inputPath" placeholder="请选择包含 .MOV 文件的文件夹" readonly>
            <template #append>
              <el-button @click="pickFolder('input')">浏览</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="输出文件夹">
          <el-input v-model="outputPath" placeholder="请选择转码后 .MP4 的输出位置" readonly>
            <template #append>
              <el-button @click="pickFolder('output')">浏览</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="scanning" :disabled="!inputPath" @click="scan">
            扫描 .MOV 文件
          </el-button>
          <el-button
            type="success"
            :loading="transcoding"
            :disabled="!canStart"
            @click="startTranscode"
            style="margin-left: 12px"
          >
            {{ transcoding ? '转码中...' : '开始转码' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 文件列表 -->
    <el-card v-if="fileList.length > 0" shadow="never" style="margin-bottom: 20px">
      <template #header>
        <span style="font-weight: 600">
          扫描结果
          <el-tag size="small" type="info" style="margin-left: 8px">{{ fileList.length }} 个文件</el-tag>
          <el-tag v-if="progressDone > 0" size="small" type="success" style="margin-left: 4px">{{ progressDone }} 已完成</el-tag>
          <el-tag v-if="progressFailed > 0" size="small" type="danger" style="margin-left: 4px">{{ progressFailed }} 失败</el-tag>
        </span>
      </template>
      <el-table :data="fileList" size="small" max-height="320" style="width: 100%">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="name" label="文件名" min-width="200" />
        <el-table-column prop="size_mb" label="大小" width="100" align="right">
          <template #default="{ row }">
            {{ row.size_mb }} MB
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.done" size="small" type="success">已完成</el-tag>
            <el-tag v-else-if="row.error" size="small" type="danger">失败</el-tag>
            <el-tag v-else-if="transcoding" size="small" type="warning">等待中</el-tag>
            <span v-else size="small">就绪</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 进度日志 -->
    <el-card v-if="logs.length > 0" shadow="never" class="progress-panel">
      <template #header>
        <span style="font-weight: 600">转码日志</span>
        <el-tag v-if="progressTotal > 0" size="small" style="margin-left: 8px">
          {{ progressDone + progressFailed }} / {{ progressTotal }}
        </el-tag>
      </template>
      <div class="log-timeline" ref="logContainer">
        <div
          v-for="(log, idx) in logs"
          :key="idx"
          class="log-entry"
          :class="{ error: log.type === 'error', success: log.type === 'complete' }"
        >
          {{ log.message }}
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'
import { selectFolder, scanMovFiles, startTranscode as apiStartTranscode, getTranscodeProgressUrl } from '../composables/useApi'
import { useSSE } from '../composables/useSSE'
import { ElMessage } from 'element-plus'

const inputPath = ref('')
const outputPath = ref('')
const fileList = ref<{ path: string; relative_path: string; name: string; size_mb: number; done?: boolean; error?: boolean }[]>([])
const scanning = ref(false)
const transcoding = ref(false)
const logs = ref<{ type: string; message: string }[]>([])
const progressTotal = ref(0)
const progressDone = ref(0)
const progressFailed = ref(0)
const logContainer = ref<HTMLElement | null>(null)
const jobId = ref('')

const canStart = computed(() => inputPath.value && outputPath.value && fileList.value.length > 0 && !transcoding.value)

async function pickFolder(type: 'input' | 'output') {
  const title = type === 'input' ? '请选择包含 .MOV 的文件夹' : '请选择输出文件夹'
  try {
    const res = await selectFolder(title)
    if (res.path) {
      if (type === 'input') {
        inputPath.value = res.path
        fileList.value = []
        logs.value = []
      } else {
        outputPath.value = res.path
      }
    }
  } catch {
    ElMessage.error('选择文件夹失败')
  }
}

async function scan() {
  if (!inputPath.value) return
  scanning.value = true
  try {
    const res = await scanMovFiles(inputPath.value)
    fileList.value = res.files.map(f => ({ ...f }))
    logs.value = []
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

async function startTranscode() {
  if (!inputPath.value || !outputPath.value) return

  // 重置进度
  fileList.value.forEach(f => { f.done = false; f.error = false })
  logs.value = []
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
        logs.value.push({ type: 'log', message: data.message })
        scrollLog()
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
        logs.value.push({ type: 'error', message: data.message })
        progressFailed.value++
        scrollLog()
      },
      complete: (data: any) => {
        logs.value.push({
          type: 'complete',
          message: data.status === 'error'
            ? '转码失败'
            : `转码完成！成功 ${data.success || 0} 个，失败 ${data.failed || 0} 个`,
        })
        progressDone.value = data.success || 0
        progressFailed.value = data.failed || 0
        transcoding.value = false
        scrollLog()
        // 断开 SSE 防止浏览器自动重连导致错误循环
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

function scrollLog() {
  setTimeout(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  }, 50)
}

onBeforeUnmount(() => {
  sse.disconnect()
})
</script>
