<template>
  <div class="stat-card glass-card">
    <div class="stat-value" :style="{ color: color }">{{ value }}</div>
    <div class="stat-label">{{ label }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  value: string | number
  label: string
  color?: string
}>()
</script>

<style scoped>
.stat-card {
  padding: var(--space-5);
  text-align: center;
}
.stat-value {
  font-size: var(--text-3xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  line-height: 1;
}
.stat-label {
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
</style>
