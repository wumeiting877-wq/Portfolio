<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { getExpense, voidExpense, type Expense } from "../../api/expenses";
import { useAuthStore } from "../../stores/auth";
import PageHeader from "../../components/PageHeader.vue";
import StatusTag from "../../components/StatusTag.vue";
import { formatMoney } from "../../utils/money";

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();
const loading = ref(false);
const expense = ref<Expense | null>(null);
const tab = ref(route.query.tab === "distributions" ? "distributions" : "overview");
const expenseId = computed(() => Number(route.params.id));

function formatDate(value: string | null | undefined) {
  return value ? value.slice(0, 10) : "-";
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "-";
  return value.replace("T", " ").slice(0, 19);
}

async function load() {
  loading.value = true;
  try {
    expense.value = await getExpense(expenseId.value);
  } finally {
    loading.value = false;
  }
}

async function switchTab(next: string) {
  tab.value = next;
  await router.replace({
    name: "expense-detail",
    params: { id: String(expenseId.value) },
    query: next === "distributions" ? { tab: "distributions" } : undefined,
  });
}

async function voidCurrent() {
  await ElMessageBox.confirm("确认作废该费用？记录会保留，不再计入有效统计。", "作废费用", { type: "warning" });
  await voidExpense(expenseId.value);
  ElMessage.success("已作废");
  await load();
}

watch(
  () => route.query.tab,
  (value) => {
    tab.value = value === "distributions" ? "distributions" : "overview";
  },
);

onMounted(load);
</script>

<template>
  <section class="list-page" v-loading="loading">
    <PageHeader :title="expense?.expense_type.name || '费用详情'" :description="expense?.description || undefined">
      <template #actions>
        <el-button @click="router.push({ name: 'expenses' })">返回列表</el-button>
        <el-button
          v-if="auth.canWriteExpenses && expense?.status === 'ACTIVE'"
          type="danger"
          @click="voidCurrent"
        >
          作废
        </el-button>
      </template>
    </PageHeader>

    <div class="product-tabs">
      <button class="product-tab" :class="{ 'is-selected': tab === 'overview' }" type="button" @click="switchTab('overview')">
        概览
      </button>
      <button
        class="product-tab"
        :class="{ 'is-selected': tab === 'distributions' }"
        type="button"
        @click="switchTab('distributions')"
      >
        费用归属
      </button>
    </div>

    <el-descriptions v-if="tab === 'overview' && expense" class="home-facts" :column="2" border>
      <el-descriptions-item label="费用类型">
        {{ expense.expense_type.name }} ({{ expense.expense_type.code }})
      </el-descriptions-item>
      <el-descriptions-item label="资源">{{ expense.resource_name || "-" }}</el-descriptions-item>
      <el-descriptions-item label="计费方式">
        <StatusTag kind="billing" :code="expense.billing_mode" />
      </el-descriptions-item>
      <el-descriptions-item label="来源">
        <StatusTag kind="source" :code="expense.source" />
      </el-descriptions-item>
      <el-descriptions-item label="费用日期">{{ formatDate(expense.expense_date) }}</el-descriptions-item>
      <el-descriptions-item label="账期">
        {{ formatDate(expense.billing_period_start) }} ~ {{ formatDate(expense.billing_period_end) }}
      </el-descriptions-item>
      <el-descriptions-item label="可见金额">
        <span class="amount-cell">{{ formatMoney(expense.currency, expense.amount) }}</span>
      </el-descriptions-item>
      <el-descriptions-item label="可见分摊合计">
        <span class="amount-cell">{{ formatMoney(expense.currency, expense.visible_allocated_amount) }}</span>
      </el-descriptions-item>
      <el-descriptions-item label="用量">{{ expense.usage_quantity || "-" }}</el-descriptions-item>
      <el-descriptions-item label="单位 / 单价">
        {{ expense.usage_unit || "-" }} / {{ expense.unit_price || "-" }}
      </el-descriptions-item>
      <el-descriptions-item label="状态">
        <StatusTag kind="expense" :code="expense.status" />
      </el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ formatDateTime(expense.created_at) }}</el-descriptions-item>
      <el-descriptions-item label="说明" :span="2">{{ expense.description || "-" }}</el-descriptions-item>
    </el-descriptions>

    <div v-if="tab === 'distributions'" class="list-panel">
      <el-table :data="expense?.distributions || []" empty-text="暂无可见分摊">
        <el-table-column label="项目" min-width="160">
          <template #default="{ row }">{{ row.project_name || "-" }}</template>
        </el-table-column>
        <el-table-column label="成员" width="160">
          <template #default="{ row }">{{ row.employee_name || "-" }}</template>
        </el-table-column>
        <el-table-column label="分摊方式" width="120">
          <template #default="{ row }">{{ row.allocation_method }}</template>
        </el-table-column>
        <el-table-column label="比例" width="100" align="right">
          <template #default="{ row }">
            <span class="amount-cell">{{ row.allocation_ratio || "-" }}</span>
          </template>
        </el-table-column>
        <el-table-column label="分摊金额" width="140" align="right">
          <template #default="{ row }">
            <span class="amount-cell">{{ row.allocated_amount }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </section>
</template>
