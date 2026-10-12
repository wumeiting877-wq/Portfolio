<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
}>();
</script>

<template>
  <header class="page-header">
    <div class="page-header__copy">
      <h1 class="page-header__title">{{ title }}</h1>
      <p v-if="description" class="page-header__description">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin: 0 0 var(--space-5);
  min-width: 0;
}

.page-header:not(:has(.page-header__description)) {
  align-items: center;
}

.page-header__copy {
  min-width: 0;
}

.page-header__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 24px;
  font-weight: 400;
  line-height: 1.33;
  letter-spacing: 0;
}

.page-header__description {
  margin: var(--space-2) 0 0;
  color: var(--color-text-secondary);
  font-size: 16px;
  font-weight: 400;
  line-height: 1.5;
  letter-spacing: 0.16px;
}

.page-header__actions {
  display: flex;
  flex-shrink: 0;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}

@media (max-width: 672px) {
  .page-header {
    flex-direction: column;
  }
}
</style>
