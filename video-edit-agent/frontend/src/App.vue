<template>
  <div class="app-layout" style="display:flex;flex:1;min-height:0">
    <aside class="app-sidebar">
      <div class="sidebar-header">
        <img src="/logo.png" class="sidebar-logo" alt="小飞龙">
        <span class="sidebar-title">小飞龙批量剪辑</span>
      </div>

      <div class="sidebar-nav">
        <el-menu :default-active="currentRoute" router>
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/project">
            <el-icon><FolderOpened /></el-icon>
            <span>项目设置</span>
          </el-menu-item>
          <el-menu-item index="/config">
            <el-icon><Setting /></el-icon>
            <span>参数配置</span>
          </el-menu-item>
          <el-menu-item index="/batch">
            <el-icon><VideoPlay /></el-icon>
            <span>批量生成</span>
          </el-menu-item>
          <el-menu-item index="/transcode">
            <el-icon><Refresh /></el-icon>
            <span>视频转码</span>
          </el-menu-item>
        </el-menu>
      </div>

      <div class="sidebar-footer">
        <div class="status-item">
          <span class="status-label">大模型</span>
          <span class="status-value">
            <span class="status-dot" :class="store.llmStatusClass" />
            {{ store.llmStatusText }}
            <el-button size="small" text type="primary" :loading="store.llmTesting" @click="store.testLLM">
              {{ store.llmTesting ? '测试' : '测试' }}
            </el-button>
          </span>
        </div>
        <div class="status-item">
          <span class="status-label">FFmpeg</span>
          <span class="status-value">
            <span class="status-dot" :class="store.ffmpegOk ? 'online' : 'offline'" />
            {{ store.ffmpegOk ? '就绪' : '未找到' }}
          </span>
        </div>
      </div>
    </aside>

    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { HomeFilled, FolderOpened, Setting, VideoPlay, Refresh } from '@element-plus/icons-vue'
import { useAppStore } from './stores/appStore'

const route = useRoute()
const store = useAppStore()
const currentRoute = computed(() => route.path)

onMounted(() => {
  store.checkServerHealth()
})
</script>
