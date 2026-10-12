<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
}>();
</script>

<template>
  <div class="empty-state">
    <p class="empty-state__title">{{ title }}</p>
    <p v-if="description" class="empty-state__description">{{ description }}</p>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  min-height: 180px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  background: var(--color-bg-panel);
}

.empty-state__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.29;
  letter-spacing: 0.16px;
}

.empty-state__description {
  margin: var(--space-2) 0 0;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.33;
  letter-spacing: 0.32px;
}
</style>
