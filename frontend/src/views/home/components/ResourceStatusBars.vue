<script setup lang="ts">
import { computed } from "vue";
import type { ResourceStatus } from "../../../api/statistics";
import EmptyState from "../../../components/EmptyState.vue";

const props = defineProps<{
  status: ResourceStatus | null;
  emptyTitle?: string;
  dimZero?: boolean;
}>();

const rows = computed(() => {
  const status = props.status;
  if (!status) return [];
  return [
    { name: "使用中", value: status.counts.ACTIVE || 0 },
    { name: "闲置", value: status.explicit_idle_count },
    { name: "未分配但仍使用中", value: status.unassigned_active_count },
    { name: "即将到期", value: status.counts.EXPIRING_SOON || 0 },
    { name: "已到期", value: status.counts.EXPIRED || 0 },
    { name: "已停用", value: status.counts.DISABLED || 0 },
  ];
});

const maxValue = computed(() => Math.max(1, ...rows.value.map((row) => row.value)));
</script>

<template>
  <div v-if="rows.length" class="status-bars">
    <div v-for="row in rows" :key="row.name" class="status-row" :class="{ 'is-zero': dimZero && row.value === 0 }">
      <span class="status-row__label">{{ row.name }}</span>
      <span class="status-row__track" aria-hidden="true">
        <span class="status-row__fill" :style="{ width: `${(row.value / maxValue) * 100}%` }" />
      </span>
      <strong class="status-row__value">{{ row.value }}</strong>
    </div>
  </div>
  <EmptyState v-else :title="emptyTitle ?? '当前没有资源数据'" />
</template>

<style scoped>
.status-bars {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.status-row {
  display: grid;
  grid-template-columns: minmax(112px, 156px) minmax(80px, 1fr) 40px;
  align-items: center;
  gap: var(--space-3);
  min-height: 24px;
  font-size: 14px;
}

.status-row__label {
  color: var(--color-text-secondary);
}

.status-row__track {
  height: 8px;
  background: var(--color-bg-subtle);
}

.status-row__fill {
  display: block;
  min-width: 0;
  height: 100%;
  background: var(--color-primary);
}

.status-row__value {
  color: var(--color-text-primary);
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.status-row.is-zero .status-row__label,
.status-row.is-zero .status-row__value {
  color: var(--color-text-muted);
  font-weight: 400;
}

.status-row.is-zero .status-row__track {
  background: var(--color-bg-page);
}

@media (max-width: 480px) {
  .status-row {
    grid-template-columns: minmax(96px, 1fr) 72px 32px;
  }
}
</style>
