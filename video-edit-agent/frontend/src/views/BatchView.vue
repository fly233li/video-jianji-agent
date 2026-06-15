<template>
  <div>
    <div class="page-header">
      <h2>批量生成</h2>
      <p>一键生成多条带货短视频</p>
    </div>

    <!-- ===== Phase: 设置 ===== -->
    <template v-if="phase === 'setup'">
      <el-card shadow="never" style="margin-bottom: 20px">
        <el-form label-width="120px">
          <el-form-item label="素材文件夹">
            <el-input :model-value="materialPath" placeholder="尚未选择" readonly>
              <template #append>
                <el-button @click="pickFolder('material')">浏览</el-button>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="输出文件夹">
            <el-input :model-value="outputPath" placeholder="尚未选择" readonly>
              <template #append>
                <el-button @click="pickFolder('output')">浏览</el-button>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item v-if="folderInfo" label="卖点数量">
            <span>{{ folderInfo.selling_points?.length || 0 }} 个卖点</span>
            <el-tag v-for="sp in folderInfo.selling_points" :key="sp" style="margin-left: 6px">
              {{ sp }}
            </el-tag>
          </el-form-item>
          <el-form-item label="商品名称">
            <el-input v-model="productName" placeholder="如: 钢制衣柜 置物架" clearable />
          </el-form-item>
          <el-form-item label="使用场景">
            <el-input v-model="usageScenario" placeholder="如: 卧室收纳 厨房置物" clearable />
          </el-form-item>
          <el-form-item label="生成数量">
            <el-input-number v-model="videoCount" :min="1" :max="500" />
            <span style="margin-left: 8px; color: #909399">条</span>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="large" :disabled="!canStart" @click="showPreview">
              预览卖点组合
            </el-button>
            <el-button v-if="!materialPath" @click="$router.push('/project')" style="margin-left: 12px">
              先去选择素材
            </el-button>
            <el-button v-if="scripts.length > 0" type="info" @click="goToScriptEdit" style="margin-left: 12px">
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
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span style="font-weight: 600">确认卖点组合</span>
            <el-tag type="info">共 {{ combinations.length }} 条视频</el-tag>
          </div>
        </template>

        <el-table :data="combinations" stripe border size="small">
          <el-table-column label="视频序号" prop="video_index" width="120" align="center" />
          <el-table-column label="卖点组合" min-width="300">
            <template #default="{ row }">
              <el-tag v-for="sp in row.selling_points" :key="sp" style="margin-right: 6px" type="primary">
                {{ sp }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>

        <div style="margin-top: 24px; text-align: center">
          <el-button size="large" @click="backToSetup">上一步</el-button>
          <el-button type="primary" size="large" @click="startScriptGeneration" style="margin-left: 16px">
            下一步 生成文案
          </el-button>
        </div>
      </el-card>
    </template>

    <!-- ===== Phase: 文案生成中 ===== -->
    <template v-else-if="phase === 'script_gen'">
      <el-card shadow="never">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span style="font-weight: 600">正在生成文案...</span>
            <el-tag type="warning" effect="dark">生成中</el-tag>
          </div>
        </template>
        <el-progress :percentage="scriptGenPercent" :stroke-width="20" :text-inside="true" />
        <div class="progress-panel" style="margin-top: 16px">
          <div class="log-timeline" ref="logRef">
            <div v-for="(entry, i) in logEntries" :key="i" class="log-entry" :class="entry.type">
              {{ entry.message }}
            </div>
          </div>
        </div>
      </el-card>
    </template>

    <!-- ===== Phase: 文案审核编辑 ===== -->
    <template v-else-if="phase === 'script_edit'">
      <el-card shadow="never" style="margin-bottom: 20px">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span style="font-weight: 600">审核文案（{{ scripts.length }} 条）</span>
            <div>
              <el-button @click="backToSetup" style="margin-right: 8px">返回</el-button>
              <el-button type="primary" :loading="rendering" @click="startRendering">
                确认无误，开始剪辑
              </el-button>
            </div>
          </div>
        </template>
        <el-alert title="请逐条检查文案内容，可以直接在文本框中修改。确认无误后点击「开始剪辑」" type="info" :closable="false" show-icon style="margin-bottom: 16px" />
      </el-card>

      <div v-for="(sc, idx) in scripts" :key="sc.video_index" style="margin-bottom: 16px">
        <el-card shadow="never">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600">
                第 {{ sc.video_index }} 条
                <el-tag size="small" style="margin-left: 8px" type="primary">
                  {{ sc.selling_points?.join(' + ') || '' }}
                </el-tag>
              </span>
              <el-button size="small" text type="primary" @click="synthesizeScript(sc)">
                预览合成
              </el-button>
              <el-button size="small" type="primary" @click="regenerate(sc)">
                重新生成
              </el-button>
            </div>
          </template>
          <el-form label-position="top" size="small">
            <el-form-item label="开头">
              <el-input v-model="sc.sections['开头']" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="卖点1">
              <el-input v-model="sc.sections['卖点1']" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="卖点2">
              <el-input v-model="sc.sections['卖点2']" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="结尾">
              <el-input v-model="sc.sections['结尾']" type="textarea" :rows="2" />
            </el-form-item>
          </el-form>
        </el-card>
      </div>

      <div style="text-align: center; margin-bottom: 40px">
        <el-button size="large" @click="backToSetup">返回</el-button>
        <el-button type="primary" size="large" :loading="rendering" @click="startRendering" style="margin-left: 16px">
          确认无误，开始剪辑
        </el-button>
      </div>
    </template>

    <!-- ===== Phase: 渲染中 / 已完成 ===== -->
    <template v-else-if="phase === 'rendering' || phase === 'done'">
      <el-card shadow="never" style="margin-bottom: 20px">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span style="font-weight: 600">
              {{ phase === 'rendering' ? '正在剪辑...' : '生成完成' }}
            </span>
            <div>
              <el-tag v-if="phase === 'rendering'" type="warning" effect="dark">进行中</el-tag>
              <el-tag v-else type="success" effect="dark">已完成</el-tag>
            </div>
          </div>
        </template>

        <el-progress
          :percentage="overallPercent"
          :status="phase === 'done' ? 'success' : undefined"
          :stroke-width="20"
          :text-inside="true"
        />

        <el-descriptions :column="3" size="small" border style="margin: 20px 0">
          <el-descriptions-item label="已完成">{{ doneCount }} / {{ totalVideos }} 条</el-descriptions-item>
          <el-descriptions-item label="成功">{{ successCount }} 条</el-descriptions-item>
          <el-descriptions-item label="失败">{{ failCount }} 条</el-descriptions-item>
          <el-descriptions-item label="已用时间">{{ elapsedText }}</el-descriptions-item>
          <el-descriptions-item label="当前视频">
            {{ currentVideo > 0 ? `第 ${currentVideo} 条` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="当前阶段">{{ currentPhase }}</el-descriptions-item>
        </el-descriptions>

        <div style="margin-bottom: 20px">
          <el-button v-if="phase === 'rendering'" type="danger" @click="cancel">取消生成</el-button>
          <el-button v-if="phase === 'done'" @click="goToScriptEdit">查看文案</el-button>
          <el-button v-if="phase === 'done'" type="primary" @click="reset">再来一批</el-button>
        </div>

        <div class="progress-panel">
          <div style="font-size: 13px; font-weight: 600; margin-bottom: 8px">运行日志</div>
          <div class="log-timeline" ref="logRef">
            <div v-for="(entry, i) in logEntries" :key="i" class="log-entry" :class="entry.type">
              {{ entry.message }}
            </div>
          </div>
        </div>
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
  getBatchHistory,
  previewBatch,
  regenerateScript as apiRegenerateScript,
  saveScripts as apiSaveScripts,
  loadScripts as apiLoadScripts,
} from '../composables/useApi'
import { useSSE } from '../composables/useSSE'
import { ElMessage, ElMessageBox } from 'element-plus'

interface ScriptItem {
  video_index: number
  selling_points: string[]
  sections: Record<string, string>
}

const route = useRoute()
const { connect, disconnect, reconnect, isConnected } = useSSE()

// ---- Setup state ----
const phase = ref<'setup' | 'review' | 'script_gen' | 'script_edit' | 'rendering' | 'done'>('setup')
const materialPath = ref('')
const outputPath = ref('')
const folderInfo = ref<any>(null)
const productName = ref('')
const usageScenario = ref('')
const videoCount = ref(5)
const combinations = ref<{ video_index: number; selling_points: string[] }[]>([])

// ---- Script generation state ----
const batchId = ref('')
const scripts = ref<ScriptItem[]>([])
const scriptGenDone = ref(0)
const scriptGenTotal = ref(0)
const scriptGenPercent = computed(() => {
  if (scriptGenTotal.value === 0) return 0
  return Math.round((scriptGenDone.value / scriptGenTotal.value) * 100)
})

// ---- Rendering state ----
const rendering = ref(false)
const totalVideos = ref(0)
const doneCount = ref(0)
const successCount = ref(0)
const failCount = ref(0)
const currentVideo = ref(0)
const currentPhase = ref('准备中')
const overallPercent = computed(() => {
  if (totalVideos.value === 0) return 0
  return Math.round((doneCount.value / totalVideos.value) * 100)
})
const startTime = ref(0)
const elapsedText = ref('00:00')

// ---- Shared ----
const logEntries = ref<{ message: string; type: string }[]>([])
const logRef = ref<HTMLDivElement | null>(null)

const canStart = computed(() => materialPath.value && outputPath.value)

// ---- Script persistence ----
const lastBatchId = ref(localStorage.getItem('lastBatchId') || '')
let saveTimer: number | null = null

async function saveScriptsToBackend() {
  if (!batchId.value || scripts.value.length === 0) return
  try {
    await apiSaveScripts(batchId.value, scripts.value)
  } catch { /* 静默失败，不阻塞用户操作 */ }
}

function saveScriptsDebounced() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = window.setTimeout(() => saveScriptsToBackend(), 2000)
}

// 自动保存：用户在编辑文案时，防抖 2 秒后写入后端文件缓存
watch(scripts, () => {
  if (phase.value === 'script_edit') {
    saveScriptsDebounced()
  }
}, { deep: true })

// Auto-scroll log
watch(logEntries, () => {
  nextTick(() => {
    if (logRef.value) {
      logRef.value.scrollTop = logRef.value.scrollHeight
    }
  })
})

// ---- Lifetime ----
onMounted(async () => {
  const saved = localStorage.getItem('projectState')
  if (saved) {
    try {
      const state = JSON.parse(saved)
      materialPath.value = state.materialPath || ''
      outputPath.value = state.outputPath || ''
      folderInfo.value = state.folderInfo || null
      productName.value = state.productName || ''
      usageScenario.value = state.usageScenario || ''
      if (state.videoCount) videoCount.value = state.videoCount
    } catch { /* ignore */ }
  }
  if (route.params.batchId) {
    batchId.value = route.params.batchId as string
    phase.value = 'setup'
  }
  // 尝试恢复上次的文案
  lastBatchId.value = localStorage.getItem('lastBatchId') || ''
  if (lastBatchId.value && scripts.value.length === 0) {
    try {
      const loaded = await apiLoadScripts(lastBatchId.value)
      if (loaded.scripts?.length > 0) {
        scripts.value = loaded.scripts
        batchId.value = lastBatchId.value
      }
    } catch { /* 静默 */ }
  }
})

onBeforeUnmount(() => {
  disconnect()
})

watch([productName, usageScenario, videoCount], saveProjectState, { immediate: false })

function saveProjectState() {
  localStorage.setItem('projectState', JSON.stringify({
    materialPath: materialPath.value,
    outputPath: outputPath.value,
    folderInfo: folderInfo.value,
    productName: productName.value,
    usageScenario: usageScenario.value,
    videoCount: videoCount.value,
  }))
}

// ---- Folder picker ----
async function pickFolder(type: 'material' | 'output') {
  const title = type === 'material' ? '请选择素材文件夹' : '请选择输出文件夹'
  try {
    const res = await selectFolder(title)
    if (!res.path) return
    if (type === 'material') {
      materialPath.value = res.path
      folderInfo.value = null
      combinations.value = []
      // 自动扫描
      try {
        const scanRes = await scanFolder(res.path)
        if (scanRes.folder_info) {
          folderInfo.value = scanRes.folder_info
        }
      } catch { /* ignore */ }
    } else {
      outputPath.value = res.path
    }
    saveProjectState()
  } catch {
    ElMessage.error('选择文件夹失败')
  }
}

// ---- Phase transitions ----
function backToSetup() {
  // 保存当前文案到后端缓存 + localStorage 标记，便于恢复
  if (batchId.value && scripts.value.length > 0) {
    localStorage.setItem('lastBatchId', batchId.value)
    lastBatchId.value = batchId.value
    saveScriptsToBackend()
  }
  phase.value = 'setup'
  combinations.value = []
}

async function showPreview() {
  if (!materialPath.value || !outputPath.value) {
    ElMessage.warning('请先选择素材文件夹和输出文件夹')
    return
  }
  try {
    const res = await previewBatch(materialPath.value, videoCount.value)
    combinations.value = res.combinations
    phase.value = 'review'
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '获取卖点组合失败')
  }
}

// ---- Phase 1: Generate Scripts ----
async function startScriptGeneration() {
  logEntries.value = []
  scripts.value = []
  scriptGenDone.value = 0
  scriptGenTotal.value = 0
  phase.value = 'script_gen'

  try {
    const res = await apiGenerateScripts(materialPath.value, videoCount.value, productName.value, usageScenario.value)
    batchId.value = res.batch_id
    scriptGenTotal.value = res.total
    logEntries.value.push({ message: `[START] 开始生成 ${res.total} 条文案...`, type: 'info' })

    // 单次 SSE 连接处理全部事件（Phase 1 + Phase 2 共用）
    connect(`/api/batch/${res.batch_id}/progress`, {
      log: (data: any) => {
        logEntries.value.push({ message: data.message || '', type: 'info' })
      },
      // --- Phase 1 事件 ---
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
        logEntries.value.push({
          message: `  [ERROR] 第 ${data.video_index} 条文案失败: ${data.message || ''}`,
          type: 'error',
        })
      },
      // 心跳保活 — 不处理
      ping: () => {},
      scripts_complete: () => {
        logEntries.value.push({ message: '[DONE] 文案生成完成，请检查编辑', type: 'success' })
        phase.value = 'script_edit'
        // 首次保存到后端缓存，后续靠防抖 watch 自动保存
        setTimeout(() => saveScriptsToBackend(), 100)
      },
      // --- Phase 2 事件 ---
      video_start: (data: any) => {
        currentVideo.value = data.video_index
        logEntries.value.push({
          message: `  [${data.video_index}/${data.total}] ${(data.selling_points || []).join(' + ')}`,
          type: 'info',
        })
      },
      video_done: (data: any) => {
        doneCount.value++
        successCount.value++
        logEntries.value.push({
          message: `  [OK] 第 ${data.video_index} 条完成 (${data.elapsed || '?'}s)`,
          type: 'success',
        })
      },
      progress: (data: any) => {
        currentPhase.value = data.phase || currentPhase.value
      },
      // --- 通用事件 ---
      error: (data: any) => {
        if (phase.value === 'rendering') {
          failCount.value++
        }
        logEntries.value.push({ message: data.message || '', type: 'error' })
      },
      complete: (data: any) => {
        phase.value = 'done'
        rendering.value = false
        totalVideos.value = data.total_videos || totalVideos.value
        // 保存 batchId 用于后续恢复文案
        localStorage.setItem('lastBatchId', batchId.value)
        lastBatchId.value = batchId.value
        logEntries.value.push({
          message: `[DONE] 完成! 成功 ${data.success} / 失败 ${data.failed}, 耗时 ${data.total_time}s`,
          type: 'success',
        })
        setTimeout(() => disconnect(), 100)
      },
      cancel: () => {
        phase.value = 'done'
        rendering.value = false
        // 保存 batchId 用于后续恢复文案
        localStorage.setItem('lastBatchId', batchId.value)
        lastBatchId.value = batchId.value
        logEntries.value.push({ message: '[CANCEL] 用户中断', type: 'error' })
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
  if (!outputPath.value) {
    ElMessage.warning('请先选择输出文件夹')
    return
  }
  if (scripts.value.length === 0) {
    ElMessage.warning('没有可渲染的文案')
    return
  }

  // 渲染前保存当前文案到后端缓存
  await saveScriptsToBackend()

  const finalScripts = scripts.value.map(sc => ({
    video_index: sc.video_index,
    selling_points: sc.selling_points,
    sections: sc.sections,
  }))

  // 检查 SSE 连接：如果断开则尝试重连（防止长时间编辑后连接超时）
  if (!isConnected.value && batchId.value) {
    logEntries.value.push({ message: '[INFO] SSE 连接已断开，尝试重新连接...', type: 'info' })
    const ok = await reconnect()
    if (!ok) {
      ElMessage.warning('SSE 连接恢复失败，渲染进度将不会实时更新')
    } else {
      logEntries.value.push({ message: '[INFO] SSE 连接已恢复', type: 'success' })
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

  logEntries.value.push({ message: `[RENDER] 开始渲染 ${finalScripts.length} 条视频...`, type: 'info' })

  try {
    await apiStartRender(batchId.value, materialPath.value, outputPath.value, finalScripts)
    // SSE 持续接收渲染事件
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '启动渲染失败')
    rendering.value = false
    phase.value = 'script_edit'
  }
}

// 从 done 页面返回文案编辑（scripts 仍保存在前端内存中）
function goToScriptEdit() {
  if (scripts.value.length === 0) {
    ElMessage.warning('没有可显示的文案')
    return
  }
  phase.value = 'script_edit'
}

// ---- Cancel / Reset ----
async function cancel() {
  try {
    await ElMessageBox.confirm('确定要取消当前任务吗？', '确认', { type: 'warning' })
    await cancelBatch(batchId.value)
    logEntries.value.push({ message: '[CANCEL] 正在取消...', type: 'error' })
  } catch { /* ignore */ }
}

function reset() {
  // 先将当前文案保存到后端缓存，以便后续恢复
  if (batchId.value && scripts.value.length > 0) {
    localStorage.setItem('lastBatchId', batchId.value)
    lastBatchId.value = batchId.value
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
  // 保留 scripts 和 batchId，这样 "恢复上次文案" 按钮仍然可用
  // 但清空 batchId 让新批次使用新的 batch_id
  batchId.value = lastBatchId.value || ''
}

function synthesizeScript(sc: ScriptItem) {
  const text = [sc.sections['开头'], sc.sections['卖点1'], sc.sections['卖点2'], sc.sections['结尾']]
    .filter(Boolean)
    .join(' | ')
  ElMessage.info(text.length > 80 ? text.slice(0, 80) + '...' : text)
}

async function regenerate(sc: ScriptItem) {
  try {
    const res = await apiRegenerateScript(
      sc.video_index,
      sc.selling_points,
      productName.value,
      usageScenario.value,
    )
    const idx = scripts.value.findIndex(s => s.video_index === sc.video_index)
    if (idx >= 0) {
      scripts.value[idx] = res
    }
    ElMessage.success(`第 ${sc.video_index} 条已重新生成`)
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '重新生成失败')
  }
}
</script>
