<script setup lang="ts">
defineProps<{
  label: string;
  modelValue: string;
  locked: boolean;
  required?: boolean;
  maxlength?: number;
  error?: string;
  helper?: string;
  actionLabel?: string;
  showAction?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
  correct: [];
}>();
</script>

<template>
  <el-form-item :error="locked ? '' : error">
    <template #label>
      {{ label }}<span v-if="required" class="field-required">*</span>
    </template>
    <div class="stable-id-field">
      <el-input
        v-if="!locked"
        :model-value="modelValue"
        :maxlength="maxlength"
        @update:model-value="emit('update:modelValue', $event)"
      />
      <el-input v-else :model-value="modelValue" disabled readonly />
      <div v-if="locked" class="stable-id-helper">
        <p class="field-hint">{{ helper || "稳定业务标识，普通编辑不可修改。" }}</p>
        <button
          v-if="showAction"
          type="button"
          class="stable-id-action"
          @click="emit('correct')"
        >
          {{ actionLabel }}
        </button>
      </div>
    </div>
  </el-form-item>
</template>

<style scoped>
.stable-id-field {
  width: 100%;
}

.stable-id-helper {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-2);
  margin-top: var(--space-1);
}

.stable-id-helper .field-hint {
  margin: 0;
  flex: 1 1 auto;
}

.stable-id-action {
  flex: 0 0 auto;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: var(--radius-none);
  background: transparent;
  box-shadow: none;
  color: var(--color-primary);
  font-family: inherit;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.33;
  letter-spacing: 0.32px;
  cursor: pointer;
}

.stable-id-action:hover {
  text-decoration: underline;
  background: var(--color-bg-page);
}

.stable-id-action:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 1px;
}

@media (max-width: 720px) {
  .stable-id-helper {
    flex-direction: column;
    align-items: stretch;
  }

  .stable-id-action {
    align-self: flex-end;
  }
}
</style>
