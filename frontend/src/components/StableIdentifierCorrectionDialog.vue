<script setup lang="ts">
import { computed, ref, watch } from "vue";
import http from "../api/http";
import { resolveApiError } from "../utils/apiError";

export type ImpactItem = {
  label: string;
  count: number;
};

export type ContextItem = {
  label: string;
  value: string;
};

const props = defineProps<{
  modelValue: boolean;
  title: string;
  impactUrl: string;
  currentLabel: string;
  currentValue: string;
  newLabel: string;
  notice: string;
  blankMessage: string;
  sameMessage: string;
  submitting?: boolean;
  error?: string;
  subjectLabel?: string;
  subjectValue?: string;
  contexts?: ContextItem[];
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  confirm: [value: string];
}>();

const nextValue = ref("");
const localError = ref("");
const impacts = ref<ImpactItem[]>([]);
const impactReady = ref(false);
const impactError = ref("");
let requestId = 0;

const referenced = computed(() => impactReady.value && impacts.value.some((item) => item.count > 0));
const shownError = computed(() => localError.value || props.error || "");

watch(
  () => props.modelValue,
  async (open) => {
    nextValue.value = "";
    localError.value = "";
    impacts.value = [];
    impactReady.value = false;
    impactError.value = "";
    if (!open) return;
    const current = ++requestId;
    try {
      const response = await http.get<{ items: ImpactItem[] }>(props.impactUrl);
      if (current !== requestId) return;
      impacts.value = response.data.items;
      impactReady.value = true;
    } catch (error: unknown) {
      if (current !== requestId) return;
      impactError.value = resolveApiError(error).message;
    }
  },
);

function close() {
  emit("update:modelValue", false);
}

function submit() {
  const next = nextValue.value.trim();
  localError.value = "";
  if (!next) {
    localError.value = props.blankMessage;
    return;
  }
  if (next === props.currentValue.trim()) {
    localError.value = props.sameMessage;
    return;
  }
  emit("confirm", next);
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    :title="title"
    width="560px"
    append-to-body
    @close="close"
  >
    <dl class="stable-id-facts">
      <div v-if="subjectLabel">
        <dt>{{ subjectLabel }}</dt>
        <dd>{{ subjectValue || "-" }}</dd>
      </div>
      <div v-for="item in contexts || []" :key="item.label">
        <dt>{{ item.label }}</dt>
        <dd>{{ item.value || "-" }}</dd>
      </div>
      <div>
        <dt>{{ currentLabel }}</dt>
        <dd>{{ currentValue || "-" }}</dd>
      </div>
    </dl>
    <el-form class="ibm-form" label-width="112px" @submit.prevent="submit">
      <el-form-item :label="newLabel" :error="shownError">
        <el-input v-model="nextValue" />
      </el-form-item>
    </el-form>
    <div class="stable-id-impact">
      <p class="stable-id-impact__label">关联影响</p>
      <p v-if="!impactReady && !impactError" class="field-hint">正在计算关联影响</p>
      <p v-else-if="impactError" class="field-hint is-error">{{ impactError }}</p>
      <ul v-else>
        <li v-for="item in impacts" :key="item.label">
          <span>{{ item.label }}</span>
          <span>{{ item.count }}</span>
        </li>
      </ul>
    </div>
    <p class="field-hint stable-id-notice">{{ notice }}</p>
    <p v-if="referenced" class="field-hint stable-id-notice">
      该标识当前已被业务数据引用。修正不会删除或重新创建已有业务记录。
    </p>
    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" :disabled="submitting || !impactReady" @click="submit">确认修正</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.stable-id-facts {
  margin: 0 0 var(--space-4);
}

.stable-id-facts div {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  gap: var(--space-2);
  padding: var(--space-1) 0;
}

.stable-id-facts dt,
.stable-id-facts dd {
  margin: 0;
  font-size: 14px;
  font-weight: 400;
  line-height: 1.29;
  letter-spacing: 0.16px;
}

.stable-id-facts dt {
  color: var(--color-text-secondary);
}

.stable-id-facts dd {
  color: var(--color-text-primary);
}

.stable-id-impact {
  margin-top: var(--space-2);
}

.stable-id-impact__label {
  margin: 0 0 var(--space-1);
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.29;
  letter-spacing: 0.16px;
}

.stable-id-impact ul {
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--color-border);
}

.stable-id-impact li {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-1) 0;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-primary);
  font-size: 14px;
  line-height: 1.29;
  letter-spacing: 0.16px;
}

.stable-id-notice {
  margin-top: var(--space-2);
}
</style>
