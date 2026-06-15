<template>
  <div>
    <PageHeader title="批量生成" description="一键生成多条带货短视频" />

    <!-- ===== Phase: 设置 ===== -->
    <template v-if="phase === 'setup'">
      <el-card shadow="never" class="mb-6">
        <el-form label-width="120px">
          <FolderPicker label="素材文件夹" v-model="store.materialPath" placeholder="尚未选择" />
          <FolderPicker label="输出文件夹" v-model="store.outputPath" placeholder="尚未选择" />
          <el-form-item v-if="store.folderInfo" label="卖点">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-sm text-muted">{{ store.folderInfo.selling_points?.length || 0 }} 个卖点</span>
              <el-tag v-for="sp in store.folderInfo.selling_points" :key="sp" size="small">
                {{ sp }}
              </el-tag>
            </div>
          </el-form-item>
          <el-form-item label="商品名称">
            <el-input v-model="store.productName" placeholder="如: 钢制衣柜 置物架" clearable />
          </el-form-item>
          <el-form-item label="使用场景">
            <el-input v-model="store.usageScenario" placeholder="如: 卧室收纳 厨房置物" clearable />
          </el-form-item>
          <el-form-item label="生成数量">
            <el-input-number v-model="store.videoCount" :min="1" :max="500" />
            <span class="text-xs text-muted ml-2">条</span>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="large" :disabled="!canStart" @click="showPreview">
              预览卖点组合
            </el-button>
            <el-button v-if="!store.materialPath" @click="$router.push('/project')" class="ml-3">
              先去选择素材
            </el-button>
            <el-button v-if="scripts.length > 0" type="info" @click="goToScriptEdit" class="ml-3">
              恢复上次文案
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </template>

    <!-- ===== Phase: 预览卖点组合 ===== -->
    <template v-else-if="phase === 'review'">
      <el-card shadow="never">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-medium">确认卖点组合</span>
            <el-tag type="info">共 {{ combinations.length }} 条</el-tag>
          </div>
        </template>
        <el-table :data="combinations" stripe border size="small">
          <el-table-column label="序号" prop="video_index" width="100" align="center" />
          <el-table-column label="卖点组合" min-width="300">
            <template #default="{ row }">
              <el-tag v-for="sp in row.selling_points" :key="sp" class="mr-2" type="primary">
                {{ sp }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div class="text-center mt-6">
          <el-button size="large" @click="phase = 'setup'">上一步</el-button>
          <el-button type="primary" size="large" @click="startScriptGeneration" class="ml-4">
            下一步，生成文案
          </el-button>
        </div>
      </el-card>
    </template>

    <!-- ===== Phase: 文案生成中 ===== -->
    <template v-else-if="phase === 'script_gen'">
      <el-card shadow="never">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-medium">正在生成文案...</span>
            <el-tag type="warning" effect="dark">生成中</el-tag>
          </div>
        </template>
        <el-progress :percentage="scriptGenPercent" :stroke-width="20" :text-inside="true" />
        <LogPanel title="生成日志" :logs="logEntries" class="mt-4" />
      </el-card>
    </template>

    <!-- ===== Phase: 文案审核编辑 ===== -->
    <template v-else-if="phase === 'script_edit'">
      <el-card shadow="never" class="mb-4">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-medium">审核文案（{{ scripts.length }} 条）</span>
            <div class="flex gap-3">
              <el-button @click="phase = 'setup'">返回</el-button>
              <el-button type="primary" :loading="rendering" @click="startRendering">
                确认无误，开始剪辑
              </el-button>
            </div>
          </div>
        </template>
        <el-alert
          title="请逐条检查文案内容，可直接在文本框中修改。确认无误后点击「开始剪辑」"
          type="info"
          :closable="false"
          show-icon
        />
      </el-card>

      <BatchScriptCard
        v-for="sc in scripts"
        :key="sc.video_index"
        :script="sc"
        @update:script="onScriptUpdate($event)"
        @preview="synthesizeScript"
        @regenerate="regenerateScript"
      />

      <div class="text-center mt-4 mb-10">
        <el-button size="large" @click="phase = 'setup'">返回</el-button>
        <el-button type="primary" size="large" :loading="rendering" @click="startRendering" class="ml-4">
          确认无误，开始剪辑
        </el-button>
      </div>
    </template>

    <!-- ===== Phase: 渲染中 / 已完成 ===== -->
    <template v-else-if="phase === 'rendering' || phase === 'done'">
      <el-card shadow="never" class="mb-6">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-medium">
              {{ phase === 'rendering' ? '正在剪辑...' : '生成完成' }}
            </span>
            <el-tag v-if="phase === 'rendering'" type="warning" effect="dark">进行中</el-tag>
            <el-tag v-else type="success" effect="dark">已完成</el-tag>
          </div>
        </template>

        <el-progress
          :percentage="overallPercent"
          :status="phase === 'done' ? 'success' : undefined"
          :stroke-width="20"
          :text-inside="true"
        />

        <el-row :gutter="16" class="mt-4 mb-4">
          <el-col :span="4">
            <StatCard :value="doneCount + '/' + totalVideos" label="已完成" color="#409eff" />
          </el-col>
          <el-col :span="4">
            <StatCard :value="successCount" label="成功" color="#67c23a" />
          </el-col>
          <el-col :span="4">
            <StatCard :value="failCount" label="失败" :color="failCount > 0 ? '#f56c6c' : '#86909c'" />
          </el-col>
          <el-col :span="4">
            <StatCard :value="elapsedText" label="已用时间" />
          </el-col>
          <el-col :span="4">
            <StatCard :value="currentVideo > 0 ? `#${currentVideo}` : '-'" label="当前视频" />
          </el-col>
          <el-col :span="4">
            <StatCard :value="currentPhase" label="当前阶段" />
          </el-col>
        </el-row>

        <div class="flex gap-3 mb-4">
          <el-button v-if="phase === 'rendering'" type="danger" @click="cancel">取消生成</el-button>
          <el-button v-if="phase === 'done'" @click="goToScriptEdit">查看文案</el-button>
          <el-button v-if="phase === 'done'" type="primary" @click="reset">再来一批</el-button>
        </div>

        <LogPanel title="运行日志" :logs="logEntries" />
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import {
  selectFolder,
  scanFolder,
  generateScripts as apiGenerateScripts,
  startRender as apiStartRender,
  cancelBatch,
  previewBatch,
  regenerateScript as apiRegenerateScript,
  saveScripts as apiSaveScripts,
  loadScripts as apiLoadScripts,
} from '../composables/useApi'
import { useSSE } from '../composables/useSSE'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import FolderPicker from '../components/FolderPicker.vue'
import LogPanel, { type LogEntry } from '../components/LogPanel.vue'
import StatCard from '../components/StatCard.vue'
import BatchScriptCard, { type ScriptItem } from '../components/BatchScriptCard.vue'
import { useProjectStore } from '../stores/projectStore'

const route = useRoute()
const store = useProjectStore()
const { connect, disconnect, reconnect, isConnected } = useSSE()

// ---- Phases ----
type Phase = 'setup' | 'review' | 'script_gen' | 'script_edit' | 'rendering' | 'done'
const phase = ref<Phase>('setup')
const combinations = ref<{ video_index: number; selling_points: string[] }[]>([])
const canStart = computed(() => store.materialPath && store.outputPath)

// ---- Script state ----
const batchId = ref('')
const scripts = ref<ScriptItem[]>([])
const scriptGenDone = ref(0)
const scriptGenTotal = ref(0)
const scriptGenPercent = computed(() =>
  scriptGenTotal.value === 0 ? 0 : Math.round((scriptGenDone.value / scriptGenTotal.value) * 100)
)

// ---- Render state ----
const rendering = ref(false)
const totalVideos = ref(0)
const doneCount = ref(0)
const successCount = ref(0)
const failCount = ref(0)
const currentVideo = ref(0)
const currentPhase = ref('准备中')
const overallPercent = computed(() =>
  totalVideos.value === 0 ? 0 : Math.round((doneCount.value / totalVideos.value) * 100)
)
const startTime = ref(0)
const elapsedText = ref('00:00')

// ---- Logs ----
const logEntries = ref<LogEntry[]>([])

// ---- Script persistence ----
const lastBatchId = ref(localStorage.getItem('lastBatchId') || '')
let saveTimer: number | null = null

function addLog(message: string, type: LogEntry['type'] = 'info') {
  logEntries.value.push({ message, type, time: new Date() })
}

async function saveScriptsToBackend() {
  if (!batchId.value || scripts.value.length === 0) return
  try { await apiSaveScripts(batchId.value, scripts.value) } catch { /* silent */ }
}

function saveScriptsDebounced() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = window.setTimeout(() => saveScriptsToBackend(), 2000)
}

watch(scripts, () => {
  if (phase.value === 'script_edit') saveScriptsDebounced()
}, { deep: true })

// ---- Script edit handlers ----
function onScriptUpdate(updated: ScriptItem) {
  const idx = scripts.value.findIndex(s => s.video_index === updated.video_index)
  if (idx >= 0) scripts.value[idx] = updated
}

function synthesizeScript(sc: ScriptItem) {
  const text = ['开头', '卖点1', '卖点2', '结尾']
    .map(k => sc.sections[k]).filter(Boolean).join(' | ')
  ElMessage.info(text.length > 80 ? text.slice(0, 80) + '...' : text)
}

async function regenerateScript(sc: ScriptItem) {
  try {
    const res = await apiRegenerateScript(
      sc.video_index, sc.selling_points, store.productName, store.usageScenario
    )
    const idx = scripts.value.findIndex(s => s.video_index === sc.video_index)
    if (idx >= 0) scripts.value[idx] = res
    ElMessage.success(`第 ${sc.video_index} 条已重新生成`)
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '重新生成失败')
  }
}

function goToScriptEdit() {
  if (scripts.value.length === 0) { ElMessage.warning('没有可显示的文案'); return }
  phase.value = 'script_edit'
}

// ---- Phase transitions ----
async function showPreview() {
  if (!store.materialPath || !store.outputPath) {
    ElMessage.warning('请先选择素材文件夹和输出文件夹')
    return
  }
  try {
    const res = await previewBatch(store.materialPath, store.videoCount)
    combinations.value = res.combinations
    phase.value = 'review'
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '获取卖点组合失败')
  }
}

// ---- Phase 1: Generate ----
async function startScriptGeneration() {
  logEntries.value = []
  scripts.value = []
  scriptGenDone.value = 0
  scriptGenTotal.value = 0
  phase.value = 'script_gen'

  try {
    const res = await apiGenerateScripts(store.materialPath, store.videoCount, store.productName, store.usageScenario)
    batchId.value = res.batch_id
    scriptGenTotal.value = res.total
    addLog(`开始生成 ${res.total} 条文案...`)

    connect(`/api/batch/${res.batch_id}/progress`, {
      log: (data: any) => addLog(data.message || ''),
      script: (data: any) => {
        scriptGenDone.value++
        scripts.value.push({
          video_index: data.video_index,
          selling_points: data.selling_points || [],
          sections: data.sections || {},
        })
      },
      script_error: (data: any) => {
        scriptGenDone.value++
        addLog(`第 ${data.video_index} 条文案失败: ${data.message || ''}`, 'error')
      },
      ping: () => {},
      scripts_complete: () => {
        addLog('文案生成完成，请检查编辑', 'success')
        phase.value = 'script_edit'
        setTimeout(() => saveScriptsToBackend(), 100)
      },
      video_start: (data: any) => {
        currentVideo.value = data.video_index
        addLog(`${data.selling_points?.join(' + ') || ''}`, 'info')
      },
      video_done: (data: any) => {
        doneCount.value++
        successCount.value++
        addLog(`第 ${data.video_index} 条完成 (${data.elapsed || '?'}s)`, 'success')
      },
      progress: (data: any) => {
        currentPhase.value = data.phase || currentPhase.value
      },
      error: (data: any) => {
        if (phase.value === 'rendering') failCount.value++
        addLog(data.message || '', 'error')
      },
      complete: (data: any) => {
        phase.value = 'done'
        rendering.value = false
        totalVideos.value = data.total_videos || totalVideos.value
        localStorage.setItem('lastBatchId', batchId.value)
        addLog(`完成! 成功 ${data.success} / 失败 ${data.failed}, 耗时 ${data.total_time}s`, 'success')
        setTimeout(() => disconnect(), 100)
      },
      cancel: () => {
        phase.value = 'done'
        rendering.value = false
        localStorage.setItem('lastBatchId', batchId.value)
        addLog('用户中断', 'error')
        disconnect()
      },
    })
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '启动文案生成失败')
    phase.value = 'review'
  }
}

// ---- Phase 2: Render ----
async function startRendering() {
  if (!store.outputPath) { ElMessage.warning('请先选择输出文件夹'); return }
  if (scripts.value.length === 0) { ElMessage.warning('没有可渲染的文案'); return }

  await saveScriptsToBackend()

  const finalScripts = scripts.value.map(sc => ({
    video_index: sc.video_index,
    selling_points: sc.selling_points,
    sections: sc.sections,
  }))

  if (!isConnected.value && batchId.value) {
    addLog('SSE 连接已断开，尝试重新连接...', 'warning')
    const ok = await reconnect()
    if (!ok) {
      ElMessage.warning('SSE 连接恢复失败，渲染进度将不会实时更新')
    } else {
      addLog('SSE 连接已恢复', 'success')
    }
  }

  doneCount.value = 0
  successCount.value = 0
  failCount.value = 0
  currentVideo.value = 0
  totalVideos.value = finalScripts.length
  startTime.value = Date.now()
  rendering.value = true
  phase.value = 'rendering'

  addLog(`开始渲染 ${finalScripts.length} 条视频...`)

  try {
    await apiStartRender(batchId.value, store.materialPath, store.outputPath, finalScripts)
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '启动渲染失败')
    rendering.value = false
    phase.value = 'script_edit'
  }
}

// ---- Cancel / Reset ----
async function cancel() {
  try {
    await ElMessageBox.confirm('确定要取消当前任务吗？', '确认', { type: 'warning' })
    await cancelBatch(batchId.value)
  } catch { /* ignore */ }
}

function reset() {
  if (batchId.value && scripts.value.length > 0) {
    localStorage.setItem('lastBatchId', batchId.value)
    saveScriptsToBackend()
  }
  disconnect()
  phase.value = 'setup'
  logEntries.value = []
  doneCount.value = 0
  successCount.value = 0
  failCount.value = 0
  currentVideo.value = 0
  totalVideos.value = 0
  scriptGenDone.value = 0
  scriptGenTotal.value = 0
  rendering.value = false
  // 保留 scripts 以便"恢复上次文案"按钮可用
  batchId.value = lastBatchId.value || ''
}

// ---- Timer ----
let timerInterval: number | null = null

watch(phase, (val) => {
  if (val === 'rendering') {
    timerInterval = window.setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime.value) / 1000)
      const m = String(Math.floor(elapsed / 60)).padStart(2, '0')
      const s = String(elapsed % 60).padStart(2, '0')
      elapsedText.value = `${m}:${s}`
    }, 1000)
  } else {
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
  }
})

// ---- Lifecycle ----
onMounted(async () => {
  if (route.params.batchId) {
    batchId.value = route.params.batchId as string
  }
  // 恢复上次文案
  lastBatchId.value = localStorage.getItem('lastBatchId') || ''
  if (lastBatchId.value && scripts.value.length === 0) {
    try {
      const loaded = await apiLoadScripts(lastBatchId.value)
      if (loaded.scripts?.length > 0) {
        scripts.value = loaded.scripts
        batchId.value = lastBatchId.value
      }
    } catch { /* silent */ }
  }
})

onBeforeUnmount(() => {
  disconnect()
  if (timerInterval) clearInterval(timerInterval)
})
</script>

<style scoped>
.ml-2 { margin-left: 8px; }
.ml-3 { margin-left: 12px; }
.ml-4 { margin-left: 16px; }
.mr-2 { margin-right: 8px; }
</style>
