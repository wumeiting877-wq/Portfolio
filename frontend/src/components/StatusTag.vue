<script setup lang="ts">
import { computed } from "vue";

type StatusKind =
  | "employee"
  | "account"
  | "role"
  | "health"
  | "project"
  | "membership"
  | "resource"
  | "allocation"
  | "expense"
  | "billing"
  | "source"
  | "notification";
type Tone = "success" | "warning" | "error" | "info" | "neutral";

const props = defineProps<{
  kind: StatusKind;
  code: string;
}>();

const EMPLOYEE_LABELS: Record<string, string> = {
  ACTIVE: "在职",
  INACTIVE: "停用",
  LEFT: "离职",
};

const ACCOUNT_LABELS: Record<string, string> = {
  ACTIVE: "启用",
  DISABLED: "停用",
  LOCKED: "锁定",
};

const ROLE_LABELS: Record<string, string> = {
  ADMIN: "管理员",
  BOSS: "老板",
  PROJECT_MANAGER: "负责人",
  MEMBER: "成员",
};

const PROJECT_LABELS: Record<string, string> = {
  PLANNING: "筹备中",
  ACTIVE: "进行中",
  PAUSED: "已暂停",
  COMPLETED: "已完成",
  ARCHIVED: "已归档",
};

const MEMBERSHIP_LABELS: Record<string, string> = {
  ACTIVE: "在项",
  INACTIVE: "已退出",
};

const RESOURCE_LABELS: Record<string, string> = {
  ACTIVE: "使用中",
  IDLE: "闲置",
  EXPIRED: "已到期",
  DISABLED: "已停用",
};

const ALLOCATION_LABELS: Record<string, string> = {
  ACTIVE: "使用中",
  INACTIVE: "已释放",
};

const EXPENSE_LABELS: Record<string, string> = {
  ACTIVE: "有效",
  VOIDED: "已作废",
};

const BILLING_LABELS: Record<string, string> = {
  RECURRING: "周期",
  ONE_TIME: "一次性",
  USAGE: "按量",
  MANUAL: "手工",
};

const SOURCE_LABELS: Record<string, string> = {
  MANUAL: "手工录入",
  RECURRING_RULE: "周期规则",
  IMPORT: "导入",
  API_SYNC: "接口同步",
};

const mapped = computed(() => {
  const code = props.code || "";

  if (props.kind === "employee") {
    const label = EMPLOYEE_LABELS[code] ?? code;
    if (code === "ACTIVE") return { label, tone: "success" as Tone };
    if (code === "INACTIVE") return { label, tone: "warning" as Tone };
    if (code === "LEFT") return { label, tone: "neutral" as Tone };
    return { label, tone: "neutral" as Tone };
  }

  if (props.kind === "account") {
    const label = ACCOUNT_LABELS[code] ?? code;
    if (code === "ACTIVE") return { label, tone: "success" as Tone };
    if (code === "DISABLED") return { label, tone: "warning" as Tone };
    if (code === "LOCKED") return { label, tone: "error" as Tone };
    return { label, tone: "neutral" as Tone };
  }

  if (props.kind === "role") {
    return {
      label: ROLE_LABELS[code] ?? code,
      tone: "neutral" as Tone,
    };
  }

  if (props.kind === "project") {
    const label = PROJECT_LABELS[code] ?? code;
    if (code === "ACTIVE") return { label, tone: "success" as Tone };
    if (code === "COMPLETED") return { label, tone: "success" as Tone };
    if (code === "PAUSED") return { label, tone: "warning" as Tone };
    if (code === "PLANNING") return { label, tone: "info" as Tone };
    return { label, tone: "neutral" as Tone };
  }

  if (props.kind === "membership") {
    const label = MEMBERSHIP_LABELS[code] ?? code;
    if (code === "ACTIVE") return { label, tone: "success" as Tone };
    return { label, tone: "neutral" as Tone };
  }

  if (props.kind === "resource") {
    if (code === "EXPIRING_SOON") return { label: "即将到期", tone: "warning" as Tone };
    const label = RESOURCE_LABELS[code] ?? code;
    if (code === "ACTIVE") return { label, tone: "success" as Tone };
    if (code === "IDLE") return { label, tone: "warning" as Tone };
    if (code === "EXPIRED") return { label, tone: "error" as Tone };
    return { label, tone: "neutral" as Tone };
  }

  if (props.kind === "allocation") {
    const label = ALLOCATION_LABELS[code] ?? code;
    if (code === "ACTIVE") return { label, tone: "success" as Tone };
    return { label, tone: "neutral" as Tone };
  }

  if (props.kind === "expense") {
    const label = EXPENSE_LABELS[code] ?? code;
    if (code === "ACTIVE") return { label, tone: "success" as Tone };
    if (code === "VOIDED") return { label, tone: "neutral" as Tone };
    return { label, tone: "neutral" as Tone };
  }

  if (props.kind === "billing") {
    return { label: BILLING_LABELS[code] ?? code, tone: "neutral" as Tone };
  }

  if (props.kind === "source") {
    return { label: SOURCE_LABELS[code] ?? code, tone: "neutral" as Tone };
  }

  if (props.kind === "notification") {
    const labels: Record<string, string> = {
      RESOURCE_EXPIRING: "即将到期",
      RESOURCE_EXPIRED: "已到期",
      RESOURCE_UNASSIGNED: "未分配",
      RECURRING_RULE_DUE: "周期待执行",
      UNREAD: "未读",
      READ: "已读",
      RESOLVED: "已处理",
    };
    const label = labels[code] ?? code;
    if (code === "RESOURCE_EXPIRED" || code === "UNREAD") return { label, tone: "warning" as Tone };
    if (code === "RESOLVED" || code === "READ") return { label, tone: "neutral" as Tone };
    if (code === "RESOURCE_EXPIRING") return { label, tone: "warning" as Tone };
    return { label, tone: "info" as Tone };
  }

  if (code === "正常" || code === "ok") {
    return { label: "正常", tone: "success" as Tone };
  }
  if (code === "不可用") {
    return { label: code, tone: "error" as Tone };
  }
  return { label: code, tone: "neutral" as Tone };
});
</script>

<template>
  <span class="status-tag" :class="`status-tag--${mapped.tone}`">
    {{ mapped.label }}
  </span>
</template>

<style scoped>
.status-tag {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  padding: var(--space-1) var(--space-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-none);
  background: var(--color-bg-panel);
  color: var(--color-text-primary);
  font-size: 12px;
  font-weight: 400;
  line-height: 1.33;
  letter-spacing: 0.32px;
  white-space: nowrap;
}

.status-tag--success {
  border-color: var(--color-success);
  color: var(--color-success);
}

.status-tag--warning {
  border-color: var(--color-warning);
  color: var(--color-text-primary);
}

.status-tag--error {
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.status-tag--info {
  border-color: var(--color-info);
  color: var(--color-text-primary);
}

.status-tag--neutral {
  border-color: var(--color-border);
  color: var(--color-text-secondary);
}
</style>
