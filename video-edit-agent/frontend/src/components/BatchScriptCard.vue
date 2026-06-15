<template>
  <el-card shadow="never" class="script-card">
    <template #header>
      <div class="flex items-center gap-3">
        <span class="font-medium">
          第 {{ script.video_index }} 条
        </span>
        <el-tag size="small" type="primary">
          {{ script.selling_points?.join(' + ') || '' }}
        </el-tag>
        <div class="flex-1" />
        <el-button size="small" text type="info" @click="$emit('preview', script)">
          预览合成
        </el-button>
        <el-button size="small" text type="primary" :loading="regenerating" @click="$emit('regenerate', script)">
          重新生成
        </el-button>
      </div>
    </template>
    <el-form label-position="top" size="small">
      <el-form-item v-for="(text, secName) in script.sections" :key="secName" :label="secName">
        <el-input
          :model-value="text"
          type="textarea"
          :rows="2"
          @input="onInput(secName, $event)"
        />
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'

export interface ScriptItem {
  video_index: number
  selling_points: string[]
  sections: Record<string, string>
}

const props = defineProps<{
  script: ScriptItem
}>()

const emit = defineEmits<{
  (e: 'update:script', val: ScriptItem): void
  (e: 'preview', val: ScriptItem): void
  (e: 'regenerate', val: ScriptItem): void
}>()

const regenerating = ref(false)

function onInput(secName: string, value: string) {
  const updated = { ...props.script }
  updated.sections = { ...updated.sections, [secName]: value }
  emit('update:script', updated)
}
</script>

<style scoped>
.script-card {
  margin-bottom: 16px;
}
</style>
