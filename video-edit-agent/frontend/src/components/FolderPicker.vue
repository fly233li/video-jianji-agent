<template>
  <el-form-item :label="label" :label-for="inputId">
    <el-input
      :id="inputId"
      :model-value="modelValue"
      :placeholder="placeholder || '请选择文件夹'"
      readonly
      clearable
      @clear="$emit('update:modelValue', '')"
    >
      <template #append>
        <el-button @click="handleBrowse" :aria-label="'浏览' + label">
          {{ browseText || '浏览' }}
        </el-button>
      </template>
    </el-input>
  </el-form-item>
</template>

<script setup lang="ts">
import { selectFolder } from '../composables/useApi'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  label: string
  modelValue: string
  placeholder?: string
  browseText?: string
  dialogTitle?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
}>()

// Generate stable unique ID for label-input association
const uid = `fp-${Math.random().toString(36).slice(2, 9)}`
const inputId = `${uid}-input`

async function handleBrowse() {
  try {
    const res = await selectFolder(props.dialogTitle || '请选择文件夹')
    if (res.path) {
      emit('update:modelValue', res.path)
    }
  } catch {
    ElMessage.error('选择文件夹失败')
  }
}
</script>
