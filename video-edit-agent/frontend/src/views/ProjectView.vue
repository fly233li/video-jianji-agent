<template>
  <div>
    <div class="page-header">
      <h2>项目设置</h2>
      <p>选择素材文件夹和输出位置</p>
    </div>

    <el-card shadow="never" style="margin-bottom: 20px">
      <el-form label-width="120px">
        <el-form-item label="素材文件夹">
          <el-input v-model="materialPath" placeholder="请选择素材主文件夹" readonly>
            <template #append>
              <el-button @click="pickFolder('material')">浏览</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="输出文件夹">
          <el-input v-model="outputPath" placeholder="请选择视频输出文件夹" readonly>
            <template #append>
              <el-button @click="pickFolder('output')">浏览</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="scanning" :disabled="!materialPath" @click="scan">
            扫描素材结构
          </el-button>
          <el-button
            type="warning"
            :loading="renaming"
            :disabled="!materialPath"
            @click="renameAll"
            style="margin-left: 12px"
          >
            重命名素材
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 扫描错误（独立显示，不受 folderInfo 为空影响） -->
    <el-alert v-if="scanError" type="error" :title="scanError" style="margin-bottom: 20px" closable @close="scanError = ''" />

    <!-- 扫描结果 -->
    <el-card v-if="folderInfo" shadow="never">
      <template #header><span style="font-weight: 600">素材结构</span></template>

      <div v-if="folderInfo.intro_folder">
        <el-tag type="warning" size="small">开头</el-tag>
        <span style="margin-left: 8px; font-size: 13px">
          {{ folderInfo.intro_folder.videos.length }} 个视频
        </span>
      </div>

      <div v-for="(sp, idx) in folderInfo.selling_points" :key="sp" style="margin-top: 8px">
        <el-tag type="primary" size="small">卖点 {{ idx + 1 }}</el-tag>
        <span style="margin-left: 8px; font-size: 13px">{{ sp }}</span>
        <span style="margin-left: 8px; font-size: 12px; color: #909399">
          ({{ folderInfo.folders?.[sp]?.videos?.length || 0 }} 个视频)
        </span>
      </div>

      <div v-if="folderInfo.outro_folder" style="margin-top: 8px">
        <el-tag type="success" size="small">结尾</el-tag>
        <span style="margin-left: 8px; font-size: 13px">
          {{ folderInfo.outro_folder.videos.length }} 个视频
        </span>
      </div>

      <div v-if="folderInfo.bgm_path" style="margin-top: 8px">
        <el-tag type="info" size="small">BGM</el-tag>
        <span style="margin-left: 8px; font-size: 13px">已配置</span>
      </div>

      <div style="margin-top: 20px">
        <el-button type="success" @click="$router.push('/batch')">
          去批量生成
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { selectFolder, scanFolder, renameVideos } from '../composables/useApi'
import { ElMessage, ElMessageBox } from 'element-plus'

const materialPath = ref('')
const outputPath = ref('')
const folderInfo = ref<any>(null)
const scanError = ref('')
const scanning = ref(false)
const renaming = ref(false)

async function pickFolder(type: 'material' | 'output') {
  const title = type === 'material' ? '请选择素材主文件夹' : '请选择视频输出文件夹'
  try {
    const res = await selectFolder(title)
    if (res.path) {
      if (type === 'material') {
        materialPath.value = res.path
        folderInfo.value = null
        scanError.value = ''
      } else {
        outputPath.value = res.path
      }
    }
  } catch {
    ElMessage.error('选择文件夹失败')
  }
}

async function scan() {
  if (!materialPath.value) return
  scanning.value = true
  scanError.value = ''
  try {
    const res = await scanFolder(materialPath.value)
    if (res.error) {
      scanError.value = res.error
      folderInfo.value = null
    } else {
      folderInfo.value = res.folder_info
    }
  } catch (err: any) {
    scanError.value = err.response?.data?.detail || '扫描失败'
    folderInfo.value = null
  } finally {
    scanning.value = false
  }
}

async function renameAll() {
  if (!materialPath.value) return
  try {
    await ElMessageBox.confirm(
      `将 ${materialPath.value} 下所有子文件夹内的视频文件重命名为 1.MP4, 2.MP4, ...？`,
      '确认重命名',
      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  renaming.value = true
  try {
    const res = await renameVideos(materialPath.value)
    if (res.renamed_count > 0) {
      ElMessage.success(`已重命名 ${res.renamed_count} 个视频文件`)
    } else {
      ElMessage.info('没有找到需要重命名的视频文件')
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '重命名失败')
  } finally {
    renaming.value = false
  }
}

// 自动保存项目状态到 localStorage
function saveState() {
  localStorage.setItem('projectState', JSON.stringify({
    materialPath: materialPath.value,
    outputPath: outputPath.value,
    folderInfo: folderInfo.value,
  }))
}
watch([materialPath, outputPath, folderInfo], saveState, { deep: true })

// 加载上次保存的状态
onMounted(() => {
  const saved = localStorage.getItem('projectState')
  if (saved) {
    try {
      const state = JSON.parse(saved)
      if (state.materialPath) materialPath.value = state.materialPath
      if (state.outputPath) outputPath.value = state.outputPath
      if (state.folderInfo) folderInfo.value = state.folderInfo
    } catch { /* ignore */ }
  }
})
</script>
