import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// === Health ===
export async function checkHealth() {
  const { data } = await api.get('/health')
  return data
}

// === Config ===
export async function getConfig() {
  const { data } = await api.get('/config')
  return data
}

export async function getConfigDefaults() {
  const { data } = await api.get('/config/defaults')
  return data
}

export async function updateConfig(values: Record<string, any>) {
  const { data } = await api.put('/config', { values })
  return data
}

// === Project ===
export async function selectFolder(title = '请选择文件夹') {
  const { data } = await api.post('/project/select-folder', { title })
  return data as { path: string | null }
}

export async function selectFile(title = '请选择 LUT 文件') {
  const { data } = await api.post('/project/select-file', { title })
  return data as { path: string | null }
}

export async function scanFolder(path: string) {
  const { data } = await api.post('/project/scan-folder', { path })
  return data as { folder_info: any | null; error: string | null }
}

// === Batch (Phase 1: Script Generation) ===
export async function generateScripts(folderPath: string, count: number, productName = '', usageScenario = '') {
  const { data } = await api.post('/batch/generate-scripts', {
    folder_path: folderPath,
    count,
    product_name: productName,
    usage_scenario: usageScenario,
  })
  return data as { batch_id: string; total: number }
}

// === Batch (Phase 2: Render) ===
export async function startRender(
  batchId: string,
  folderPath: string,
  outputPath: string,
  scripts: { video_index: number; selling_points: string[]; sections: Record<string, string> }[],
) {
  const { data } = await api.post('/batch/start-render', {
    batch_id: batchId,
    folder_path: folderPath,
    output_path: outputPath,
    scripts,
  })
  return data as { status: string; total: number }
}

// === Script persistence (实时热更新) ===
export async function saveScripts(
  batchId: string,
  scripts: { video_index: number; selling_points: string[]; sections: Record<string, string> }[],
) {
  const { data } = await api.put(`/batch/${batchId}/scripts`, { scripts })
  return data as { status: string }
}

export async function loadScripts(batchId: string) {
  const { data } = await api.get(`/batch/${batchId}/scripts`)
  return data as { scripts: { video_index: number; selling_points: string[]; sections: Record<string, string> }[] }
}

// (old startBatch kept for reference, no longer used by new UI)
export async function startBatch(folderPath: string, outputPath: string, count: number, productName = '', usageScenario = '') {
  const { data } = await api.post('/batch/start', {
    folder_path: folderPath,
    output_path: outputPath,
    count,
    product_name: productName,
    usage_scenario: usageScenario,
  })
  return data as { batch_id: string; total_videos: number; status: string }
}

export async function getBatchStatus(batchId: string) {
  const { data } = await api.get(`/batch/${batchId}/status`)
  return data
}

export async function cancelBatch(batchId: string) {
  const { data } = await api.post(`/batch/${batchId}/cancel`)
  return data
}

export async function getBatchHistory(limit = 10) {
  const { data } = await api.get('/batch/history', { params: { limit } })
  return data as { history: any[] }
}

export function getBatchProgressUrl(batchId: string) {
  return `${api.defaults.baseURL}/batch/${batchId}/progress`
}

// === Batch Preview ===
export async function previewBatch(folderPath: string, count: number) {
  const { data } = await api.post('/batch/preview', { folder_path: folderPath, count })
  return data as {
    combinations: { video_index: number; selling_points: string[] }[]
    total_combos: number
    total_videos: number
  }
}

// === Regenerate single script ===
export async function regenerateScript(videoIndex: number, sellingPoints: string[], productName = '', usageScenario = '') {
  const { data } = await api.post('/batch/regenerate-script', {
    video_index: videoIndex,
    selling_points: sellingPoints,
    product_name: productName,
    usage_scenario: usageScenario,
  })
  return data as { video_index: number; selling_points: string[]; sections: Record<string, string> }
}

// === Rename ===
export async function renameVideos(folderPath: string) {
  const { data } = await api.post('/project/rename-videos', { folder_path: folderPath })
  return data as { renamed_count: number; files: string[] }
}

// === LLM Check ===
export async function checkLLM() {
  const { data } = await api.post('/check-llm')
  return data as { status: string; latency_ms: number | null; level: string; message: string }
}

// === Transcode ===
export async function scanMovFiles(folderPath: string) {
  const { data } = await api.post('/transcode/scan', { path: folderPath })
  return data as { files: { path: string; relative_path: string; name: string; size_mb: number }[]; total: number }
}

export async function startTranscode(inputFolder: string, outputFolder: string) {
  const { data } = await api.post('/transcode/start', {
    input_folder: inputFolder,
    output_folder: outputFolder,
  })
  return data as { job_id: string; total: number }
}

export function getTranscodeProgressUrl(jobId: string) {
  return `${api.defaults.baseURL}/transcode/${jobId}/progress`
}
