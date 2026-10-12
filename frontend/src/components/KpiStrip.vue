<script setup lang="ts">
export type KpiItem = {
  label: string;
  value?: string;
  lines?: string[];
};

defineProps<{
  items: KpiItem[];
  columns?: number;
}>();
</script>

<template>
  <div
    class="kpi-strip"
    :class="{ 'is-fixed': columns }"
    :style="columns ? { '--kpi-columns': String(columns) } : undefined"
  >
    <div v-for="item in items" :key="item.label" class="kpi-cell">
      <div class="kpi-label">{{ item.label }}</div>
      <div v-if="item.lines?.length" class="kpi-lines">
        <div v-for="line in item.lines" :key="line" class="kpi-line">{{ line }}</div>
      </div>
      <div v-else class="kpi-value">{{ item.value ?? "-" }}</div>
    </div>
  </div>
</template>

<style scoped>
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  border: 1px solid var(--color-border);
  background: var(--color-bg-panel);
}

.kpi-cell {
  min-width: 0;
  padding: 12px 16px;
  border-right: 1px solid var(--color-border);
}

.kpi-cell:last-child {
  border-right: 0;
}

.kpi-label {
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 400;
  line-height: 1.33;
  letter-spacing: 0.32px;
}

.kpi-value,
.kpi-line {
  margin-top: var(--space-2);
  color: var(--color-text-primary);
  font-size: 24px;
  font-weight: 400;
  line-height: 1.33;
  letter-spacing: 0;
  font-variant-numeric: tabular-nums;
}

.kpi-line {
  font-size: 20px;
}

.kpi-lines {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kpi-strip.is-fixed {
  grid-template-columns: repeat(var(--kpi-columns), minmax(0, 1fr));
}

.kpi-strip.is-fixed .kpi-value,
.kpi-strip.is-fixed .kpi-line {
  font-size: clamp(14px, 1.15vw, 20px);
  white-space: nowrap;
}

@media (max-width: 1024px) {
  .kpi-strip:not(.is-fixed) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .kpi-strip:not(.is-fixed) .kpi-cell:nth-child(2n) {
    border-right: 0;
  }

  .kpi-strip:not(.is-fixed) .kpi-cell {
    border-bottom: 1px solid var(--color-border);
  }
}

@media (max-width: 672px) {
  .kpi-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
