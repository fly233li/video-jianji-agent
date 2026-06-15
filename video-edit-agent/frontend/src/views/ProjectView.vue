<template>
  <div>
    <PageHeader title="项目设置" description="选择素材文件夹和输出位置" />

    <el-card shadow="never" class="mb-6">
      <el-form label-width="120px">
        <FolderPicker
          label="素材文件夹"
          v-model="store.materialPath"
          placeholder="请选择素材主文件夹"
          dialog-title="请选择素材主文件夹"
        />
        <FolderPicker
          label="输出文件夹"
          v-model="store.outputPath"
          placeholder="请选择视频输出文件夹"
          dialog-title="请选择视频输出文件夹"
        />
        <el-form-item>
          <el-button type="primary" :loading="store.scanning" :disabled="!store.materialPath" @click="store.scan">
            {{ store.scanning ? '扫描中...' : '扫描素材结构' }}
          </el-button>
          <el-button
            type="warning"
            :loading="store.renaming"
            :disabled="!store.materialPath"
            @click="store.renameAll"
            class="ml-3"
          >
            {{ store.renaming ? '重命名中...' : '重命名素材' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-alert v-if="store.scanError" type="error" :title="store.scanError" class="mb-6" closable @close="store.scanError = ''" />

    <!-- Loading skeleton -->
    <el-card v-if="store.scanning && !store.folderInfo" shadow="never">
      <template #header><span class="font-medium">素材结构</span></template>
      <div class="empty-state">
        <el-skeleton :rows="3" animated />
      </div>
    </el-card>

    <!-- Scan results -->
    <el-card v-if="store.folderInfo" shadow="never">
      <template #header>
        <span class="font-medium">素材结构</span>
        <el-tag size="small" type="success" class="ml-3">已扫描</el-tag>
      </template>

      <div class="flex items-center gap-4 flex-wrap">
        <div v-if="store.folderInfo.intro_folder" class="flex items-center gap-2">
          <el-tag type="warning" size="small">开头</el-tag>
          <span class="text-sm">{{ store.folderInfo.intro_folder.videos.length }} 个视频</span>
        </div>

        <div v-for="(sp, idx) in store.folderInfo.selling_points" :key="sp" class="flex items-center gap-2">
          <el-tag type="primary" size="small">卖点 {{ idx + 1 }}</el-tag>
          <span class="text-sm">{{ sp }}</span>
          <span class="text-xs text-muted">({{ store.folderInfo.folders?.[sp]?.videos?.length || 0 }} 个视频)</span>
        </div>

        <div v-if="store.folderInfo.outro_folder" class="flex items-center gap-2">
          <el-tag type="success" size="small">结尾</el-tag>
          <span class="text-sm">{{ store.folderInfo.outro_folder.videos.length }} 个视频</span>
        </div>

        <div v-if="store.folderInfo.bgm_path" class="flex items-center gap-2">
          <el-tag type="info" size="small">BGM</el-tag>
          <span class="text-sm">已配置</span>
        </div>
      </div>

      <div class="mt-4">
        <el-button type="success" @click="$router.push('/batch')">
          去批量生成
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import PageHeader from '../components/PageHeader.vue'
import FolderPicker from '../components/FolderPicker.vue'
import { useProjectStore } from '../stores/projectStore'

const store = useProjectStore()
</script>

<style scoped>
.ml-3 { margin-left: 12px; }
</style>
