import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { selectFolder, scanFolder, renameVideos } from '../composables/useApi'
import { ElMessage, ElMessageBox } from 'element-plus'

const STORAGE_KEY = 'projectState'

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}

export const useProjectStore = defineStore('project', () => {
  const saved = loadFromStorage()

  const materialPath = ref(saved?.materialPath || '')
  const outputPath = ref(saved?.outputPath || '')
  const folderInfo = ref<any>(saved?.folderInfo || null)
  const productName = ref(saved?.productName || '')
  const usageScenario = ref(saved?.usageScenario || '')
  const videoCount = ref(saved?.videoCount || 5)
  const scanError = ref('')
  const scanning = ref(false)
  const renaming = ref(false)

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      materialPath: materialPath.value,
      outputPath: outputPath.value,
      folderInfo: folderInfo.value,
      productName: productName.value,
      usageScenario: usageScenario.value,
      videoCount: videoCount.value,
    }))
  }

  watch([materialPath, outputPath, folderInfo, productName, usageScenario, videoCount], persist, { deep: true })

  async function pickFolder(type: 'material' | 'output') {
    const title = type === 'material' ? '请选择素材主文件夹' : '请选择视频输出文件夹'
    try {
      const res = await selectFolder(title)
      if (!res.path) return
      if (type === 'material') {
        materialPath.value = res.path
        folderInfo.value = null
        scanError.value = ''
      } else {
        outputPath.value = res.path
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
    } catch { return }
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

  return {
    materialPath, outputPath, folderInfo,
    productName, usageScenario, videoCount,
    scanError, scanning, renaming,
    pickFolder, scan, renameAll,
  }
})
