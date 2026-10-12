<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { listEmployees, type Employee } from "../../api/employees";
import { listProjects, type Project } from "../../api/projects";
import { listResources, type Resource } from "../../api/resources";
import {
  correctExpenseTypeCode,
  createExpense,
  createExpenseType,
  disableExpenseType,
  enableExpenseType,
  listExpenseTypes,
  listExpenses,
  listSuggestedDistributions,
  updateExpense,
  updateExpenseType,
  voidExpense,
  type Expense,
  type ExpenseDistributionInput,
  type ExpenseType,
} from "../../api/expenses";
import { useRouteTitle } from "../../composables/roleUi";
import { useAuthStore } from "../../stores/auth";
import PageHeader from "../../components/PageHeader.vue";
import StableIdentifierCorrectionDialog from "../../components/StableIdentifierCorrectionDialog.vue";
import StableIdentifierField from "../../components/StableIdentifierField.vue";
import StatusTag from "../../components/StatusTag.vue";
import { applyApiFieldErrors, resolveApiError } from "../../utils/apiError";
import { amountScale, hasText } from "../../utils/formRules";
import { currencyLabel } from "../../utils/money";

type DistRow = {
  project_id?: number;
  employee_id?: number;
  allocation_method: string;
  allocation_ratio: string;
  allocated_amount: string;
};

const auth = useAuthStore();
const pageTitle = useRouteTitle("expenses");
const route = useRoute();
const router = useRouter();
const loading = ref(false);
const keyword = ref("");
const typeFilter = ref<number | undefined>(undefined);
const billingFilter = ref("");
const projectFilter = ref<number | undefined>(undefined);
const employeeFilter = ref<number | undefined>(undefined);
const currencyFilter = ref("");
const statusFilter = ref("ACTIVE");
const dateFrom = ref("");
const dateTo = ref("");
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);
const rows = ref<Expense[]>([]);
const expenseTypes = ref<ExpenseType[]>([]);
const projects = ref<Project[]>([]);
const employees = ref<Employee[]>([]);
const resources = ref<Resource[]>([]);
const dialogVisible = ref(false);
const typeDialogVisible = ref(false);
const editingId = ref<number | null>(null);
const editingTypeId = ref<number | null>(null);
const form = reactive({
  expense_type_id: undefined as number | undefined,
  resource_account_id: undefined as number | undefined,
  billing_mode: "MANUAL",
  expense_date: "",
  billing_period_start: "" as string,
  billing_period_end: "" as string,
  amount: "",
  currency: "CNY",
  usage_quantity: "",
  usage_unit: "",
  unit_price: "",
  description: "",
});
const errors = reactive({
  expense_type_id: "",
  resource_account_id: "",
  billing_mode: "",
  expense_date: "",
  amount: "",
  currency: "",
  targets: "",
});
const distRows = ref<DistRow[]>([emptyDist()]);
const typeForm = reactive({
  code: "",
  name: "",
  category: "SOFTWARE",
  description: "",
});
const codeDialogVisible = ref(false);
const codeError = ref("");
const correctingCode = ref(false);

const billingOptions = [
  { value: "RECURRING", label: "周期" },
  { value: "ONE_TIME", label: "一次性" },
  { value: "USAGE", label: "按量" },
  { value: "MANUAL", label: "手工" },
];
const categoryOptions = [
  { value: "SUBSCRIPTION", label: "订阅" },
  { value: "ONE_TIME", label: "一次性" },
  { value: "API_USAGE", label: "API 按量" },
  { value: "SERVER", label: "服务器" },
  { value: "DOMAIN", label: "域名" },
  { value: "CLOUD_SERVICE", label: "云服务" },
  { value: "SOFTWARE", label: "软件" },
  { value: "HARDWARE", label: "硬件" },
  { value: "OTHER", label: "其他" },
];
const methodOptions = [
  { value: "DIRECT", label: "直接归属" },
  { value: "EQUAL", label: "平均" },
  { value: "RATIO", label: "比例" },
  { value: "MANUAL", label: "手工金额" },
];

const showEmployeeFilter = computed(() => auth.role !== "MEMBER" && auth.canViewEmployees);

function emptyDist(): DistRow {
  return {
    project_id: undefined,
    employee_id: undefined,
    allocation_method: "DIRECT",
    allocation_ratio: "",
    allocated_amount: "",
  };
}

function formatDate(value: string | null) {
  return value ? value.slice(0, 10) : "-";
}

function formatAmount(value: string | null | undefined) {
  if (!value) return "-";
  return value;
}

const distributionSum = computed(() => {
  return distRows.value.reduce((sum, row) => {
    const resolved = resolvedAllocatedAmount(row);
    const scaled = amountScale(resolved || "");
    if (scaled === null) return sum;
    return sum + Number(scaled) / 10000;
  }, 0);
});

const distributionMatches = computed(() => {
  if (!form.amount) return false;
  return Math.abs(distributionSum.value - Number(form.amount)) < 0.0000001;
});

async function loadTypes() {
  expenseTypes.value = await listExpenseTypes({ include_inactive: auth.canWriteExpenses });
}

async function load() {
  loading.value = true;
  try {
    const result = await listExpenses({
      keyword: keyword.value || undefined,
      expense_type_id: typeFilter.value,
      billing_mode: billingFilter.value || undefined,
      project_id: projectFilter.value,
      employee_id: employeeFilter.value,
      currency: currencyFilter.value || undefined,
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
      status: statusFilter.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    });
    rows.value = result.items;
    total.value = result.total;
    page.value = result.page;
    pageSize.value = result.page_size;
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  keyword.value = "";
  typeFilter.value = undefined;
  billingFilter.value = "";
  projectFilter.value = undefined;
  employeeFilter.value = undefined;
  currencyFilter.value = "";
  statusFilter.value = "ACTIVE";
  dateFrom.value = "";
  dateTo.value = "";
  page.value = 1;
  void load();
}

function goDetail(row: Expense) {
  void router.push({ name: "expense-detail", params: { id: String(row.id) } });
}

function clearErrors() {
  errors.expense_type_id = "";
  errors.resource_account_id = "";
  errors.billing_mode = "";
  errors.expense_date = "";
  errors.amount = "";
  errors.currency = "";
  errors.targets = "";
}

function openCreate() {
  editingId.value = null;
  clearErrors();
  form.expense_type_id = undefined;
  form.resource_account_id = undefined;
  form.billing_mode = "MANUAL";
  form.expense_date = "";
  form.billing_period_start = "";
  form.billing_period_end = "";
  form.amount = "";
  form.currency = "CNY";
  form.usage_quantity = "";
  form.usage_unit = "";
  form.unit_price = "";
  form.description = "";
  distRows.value = [emptyDist()];
  dialogVisible.value = true;
}

function openEdit(row: Expense) {
  editingId.value = row.id;
  clearErrors();
  form.expense_type_id = row.expense_type.id;
  form.resource_account_id = row.resource_account_id ?? undefined;
  form.billing_mode = row.billing_mode;
  form.expense_date = row.expense_date;
  form.billing_period_start = row.billing_period_start || "";
  form.billing_period_end = row.billing_period_end || "";
  form.amount = row.amount;
  form.currency = row.currency;
  form.usage_quantity = row.usage_quantity || "";
  form.usage_unit = row.usage_unit || "";
  form.unit_price = row.unit_price || "";
  form.description = row.description || "";
  distRows.value = row.distributions.map((item) => ({
    project_id: item.project_id ?? undefined,
    employee_id: item.employee_id ?? undefined,
    allocation_method: item.allocation_method,
    allocation_ratio: item.allocation_ratio || "",
    allocated_amount: item.allocated_amount,
  }));
  dialogVisible.value = true;
}

function addDistRow() {
  distRows.value.push(emptyDist());
}

function removeDistRow(index: number) {
  distRows.value.splice(index, 1);
  if (!distRows.value.length) distRows.value = [emptyDist()];
}

function resolvedAllocatedAmount(row: DistRow): string | null {
  if (hasText(row.allocated_amount)) return row.allocated_amount.trim();
  const singleDirect =
    distRows.value.length === 1 &&
    (row.allocation_method === "DIRECT" || row.allocation_method === "MANUAL") &&
    hasText(form.amount);
  if (singleDirect) return form.amount.trim();
  return null;
}

function toDistributions(): ExpenseDistributionInput[] {
  return distRows.value.map((row) => ({
    project_id: row.project_id ?? null,
    employee_id: row.employee_id ?? null,
    allocation_method: row.allocation_method,
    allocation_ratio: row.allocation_ratio || null,
    allocated_amount: resolvedAllocatedAmount(row),
  }));
}

function validateDistributions() {
  errors.targets = "";
  if (!distRows.value.length) {
    errors.targets = "项目 / 人员至少选择一项";
    return false;
  }
  for (const row of distRows.value) {
    if (!row.project_id && !row.employee_id) {
      errors.targets = "项目 / 人员至少选择一项";
      return false;
    }
    if (hasText(row.allocated_amount)) {
      const scaled = amountScale(row.allocated_amount);
      if (scaled === null || scaled < 0n) {
        errors.targets = scaled !== null && scaled < 0n ? "金额不能为负数" : "分摊金额不能为空";
        return false;
      }
    }
    if (row.allocation_method === "RATIO" && !hasText(row.allocation_ratio) && !hasText(row.allocated_amount)) {
      errors.targets = "按比例分摊必须提供比例";
      return false;
    }
  }
  const methods = new Set(distRows.value.map((row) => row.allocation_method));
  const amountsEmpty = distRows.value.every((row) => !hasText(row.allocated_amount));
  const backendSplit =
    methods.size === 1 && amountsEmpty && (methods.has("EQUAL") || methods.has("RATIO"));
  if (backendSplit) return true;
  const missingAmount = distRows.value.some((row) => !resolvedAllocatedAmount(row));
  if (missingAmount) {
    errors.targets = "分摊金额不能为空";
    return false;
  }
  const total = amountScale(form.amount);
  const sum = distRows.value.reduce((acc, row) => acc + (amountScale(resolvedAllocatedAmount(row)) || 0n), 0n);
  if (total !== null && sum !== total) {
    errors.targets = "分摊金额合计必须等于费用金额";
    return false;
  }
  return true;
}

function validateForm() {
  clearErrors();
  if (!form.expense_type_id) errors.expense_type_id = "请选择费用类型";
  if (!hasText(form.billing_mode)) errors.billing_mode = "请选择计费方式";
  if (!hasText(form.expense_date)) errors.expense_date = "请选择费用日期";
  if (!hasText(form.amount)) errors.amount = "请输入金额";
  else if (amountScale(form.amount) === null) errors.amount = "请输入金额";
  else if ((amountScale(form.amount) || 0n) < 0n) errors.amount = "金额不能为负数";
  if (!hasText(form.currency)) errors.currency = "请选择币种";
  const fieldsReady =
    !errors.expense_type_id &&
    !errors.billing_mode &&
    !errors.expense_date &&
    !errors.amount &&
    !errors.currency;
  const distributionsReady = validateDistributions();
  return fieldsReady && distributionsReady;
}

async function save() {
  if (!validateForm() || !form.expense_type_id) return;
  const payload = {
    expense_type_id: form.expense_type_id,
    resource_account_id: form.resource_account_id ?? null,
    billing_mode: form.billing_mode,
    expense_date: form.expense_date,
    billing_period_start: form.billing_period_start || null,
    billing_period_end: form.billing_period_end || null,
    amount: form.amount.trim(),
    currency: form.currency,
    usage_quantity: form.usage_quantity || null,
    usage_unit: form.usage_unit || null,
    unit_price: form.unit_price || null,
    description: form.description,
    distributions: toDistributions(),
  };
  try {
    if (editingId.value) {
      await updateExpense(editingId.value, payload);
      ElMessage.success("已保存");
    } else {
      await createExpense(payload);
      ElMessage.success("已新增");
    }
  } catch (error: unknown) {
    applyApiFieldErrors(error, errors);
    return;
  }
  dialogVisible.value = false;
  await load();
}

async function voidRow(row: Expense) {
  await ElMessageBox.confirm("确认作废该费用？记录会保留，不再计入有效统计。", "作废费用", { type: "warning" });
  await voidExpense(row.id);
  ElMessage.success("已作废");
  await load();
}

async function suggestFromResource() {
  if (!form.resource_account_id || !form.amount) {
    ElMessage.warning("请先选择资源并填写金额");
    return;
  }
  const suggestions = await listSuggestedDistributions(form.resource_account_id, form.amount);
  if (!suggestions.length) {
    ElMessage.warning("该资源没有有效分配，无法生成建议");
    return;
  }
  distRows.value = suggestions.map((item) => ({
    project_id: item.project_id ?? undefined,
    employee_id: item.employee_id ?? undefined,
    allocation_method: item.allocation_method,
    allocation_ratio: item.allocation_ratio || "",
    allocated_amount: item.allocated_amount,
  }));
}

function openTypeManager() {
  editingTypeId.value = null;
  typeForm.code = "";
  typeForm.name = "";
  typeForm.category = "SOFTWARE";
  typeForm.description = "";
  typeDialogVisible.value = true;
}

function editType(row: ExpenseType) {
  editingTypeId.value = row.id;
  typeForm.code = row.code;
  typeForm.name = row.name;
  typeForm.category = row.category;
  typeForm.description = row.description || "";
}

function openCodeCorrection() {
  if (auth.role !== "ADMIN" || !editingTypeId.value) return;
  codeError.value = "";
  codeDialogVisible.value = true;
}

async function submitCodeCorrection(nextValue: string) {
  if (!editingTypeId.value || correctingCode.value) return;
  correctingCode.value = true;
  codeError.value = "";
  try {
    const updated = await correctExpenseTypeCode(editingTypeId.value, nextValue);
    typeForm.code = updated.code;
    ElMessage.success("编码已修正");
    codeDialogVisible.value = false;
    await loadTypes();
  } catch (error: unknown) {
    codeError.value = resolveApiError(error).message;
  } finally {
    correctingCode.value = false;
  }
}

async function saveType() {
  if (editingTypeId.value) {
    await updateExpenseType(editingTypeId.value, {
      name: typeForm.name,
      category: typeForm.category,
      description: typeForm.description,
    });
  } else {
    await createExpenseType({
      code: typeForm.code,
      name: typeForm.name,
      category: typeForm.category,
      description: typeForm.description,
    });
  }
  ElMessage.success("已保存费用类型");
  editingTypeId.value = null;
  typeForm.code = "";
  typeForm.name = "";
  typeForm.description = "";
  await loadTypes();
}

async function toggleType(row: ExpenseType) {
  if (row.is_active) await disableExpenseType(row.id);
  else await enableExpenseType(row.id);
  await loadTypes();
}

onMounted(async () => {
  const qid = Number(route.query.employee_id);
  if (Number.isFinite(qid) && qid > 0) {
    employeeFilter.value = qid;
  }
  await loadTypes();
  projects.value = (await listProjects({ page: 1, page_size: 100 })).items;
  resources.value = (await listResources({ page: 1, page_size: 100 })).items;
  if (auth.canViewEmployees) {
    employees.value = await listEmployees({ employment_status: "ACTIVE" });
  }
  await load();
});
</script>

<template>
  <section class="list-page">
    <PageHeader :title="pageTitle" description="查看费用记录与归属分摊。金额按当前权限范围显示。">
      <template v-if="auth.canWriteExpenses" #actions>
        <el-button @click="openTypeManager">费用类型</el-button>
        <el-button type="primary" @click="openCreate">新增费用</el-button>
      </template>
    </PageHeader>

    <div class="list-toolbar">
      <el-input v-model="keyword" class="list-toolbar__search" placeholder="说明或类型" @keyup.enter="load" />
      <el-select v-model="typeFilter" clearable placeholder="费用类型" class="list-toolbar__status">
        <el-option
          v-for="item in expenseTypes.filter((type) => type.is_active)"
          :key="item.id"
          :label="item.name"
          :value="item.id"
        />
      </el-select>
      <el-select v-model="billingFilter" clearable placeholder="计费方式" class="list-toolbar__status">
        <el-option v-for="item in billingOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-select v-model="projectFilter" clearable filterable placeholder="项目" class="list-toolbar__status">
        <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select
        v-if="showEmployeeFilter"
        v-model="employeeFilter"
        clearable
        filterable
        placeholder="成员"
        class="list-toolbar__status"
      >
        <el-option
          v-for="item in employees"
          :key="item.id"
          :label="`${item.name} (${item.employee_no})`"
          :value="item.id"
        />
      </el-select>
      <el-select v-model="currencyFilter" clearable placeholder="币种" class="list-toolbar__status">
        <el-option label="人民币" value="CNY" />
        <el-option label="美元" value="USD" />
      </el-select>
      <el-select v-model="statusFilter" clearable placeholder="状态" class="list-toolbar__status">
        <el-option label="有效" value="ACTIVE" />
        <el-option label="已作废" value="VOIDED" />
      </el-select>
      <el-date-picker v-model="dateFrom" type="date" value-format="YYYY-MM-DD" placeholder="开始日期" />
      <el-date-picker v-model="dateTo" type="date" value-format="YYYY-MM-DD" placeholder="结束日期" />
      <el-button @click="load">查询</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <div class="list-panel">
      <el-table :data="rows" v-loading="loading" empty-text="暂无数据">
        <el-table-column label="费用日期" width="120">
          <template #default="{ row }">{{ formatDate(row.expense_date) }}</template>
        </el-table-column>
        <el-table-column label="费用类型" min-width="140">
          <template #default="{ row }">{{ row.expense_type.name }}</template>
        </el-table-column>
        <el-table-column label="资源" min-width="140">
          <template #default="{ row }">{{ row.resource_name || "-" }}</template>
        </el-table-column>
        <el-table-column label="计费方式" width="100">
          <template #default="{ row }"><StatusTag kind="billing" :code="row.billing_mode" /></template>
        </el-table-column>
        <el-table-column label="可见归属" min-width="160">
          <template #default="{ row }">{{ row.visible_attribution || "-" }}</template>
        </el-table-column>
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }">
            <span class="amount-cell">{{ formatAmount(row.amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="币种" width="88"><template #default="{ row }">{{ currencyLabel(row.currency) }}</template></el-table-column>
        <el-table-column label="来源" width="110">
          <template #default="{ row }"><StatusTag kind="source" :code="row.source" /></template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }"><StatusTag kind="expense" :code="row.status" /></template>
        </el-table-column>
        <el-table-column label="操作" :width="auth.canWriteExpenses ? 160 : 88" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="goDetail(row)">查看</el-button>
            <template v-if="auth.canWriteExpenses && row.status === 'ACTIVE'">
              <el-button text type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button text type="danger" @click="voidRow(row)">作废</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
      <div class="list-pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="load"
          @size-change="load"
        />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑费用' : '新增费用'" width="760px">
      <el-form class="ibm-form" label-width="96px">
        <el-form-item :error="errors.expense_type_id">
          <template #label>费用类型<span class="field-required">*</span></template>
          <el-select v-model="form.expense_type_id" filterable style="width: 100%">
            <el-option
              v-for="item in expenseTypes"
              :key="item.id"
              :label="item.is_active ? `${item.name} (${item.code})` : `${item.name} (${item.code}) · 已停用`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="资源账号" :error="errors.resource_account_id">
          <el-select v-model="form.resource_account_id" clearable filterable style="width: 100%">
            <el-option
              v-for="item in resources"
              :key="item.id"
              :label="item.resource_name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :error="errors.billing_mode">
          <template #label>计费方式<span class="field-required">*</span></template>
          <el-select v-model="form.billing_mode" clearable style="width: 100%">
            <el-option v-for="item in billingOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item :error="errors.expense_date">
          <template #label>费用日期<span class="field-required">*</span></template>
          <el-date-picker v-model="form.expense_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="账期开始">
          <el-date-picker v-model="form.billing_period_start" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="账期结束">
          <el-date-picker v-model="form.billing_period_end" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item :error="errors.amount">
          <template #label>金额<span class="field-required">*</span></template>
          <el-input v-model="form.amount" />
        </el-form-item>
        <el-form-item :error="errors.currency">
          <template #label>币种<span class="field-required">*</span></template>
          <el-select v-model="form.currency" clearable style="width: 100%">
            <el-option label="人民币" value="CNY" />
            <el-option label="美元" value="USD" />
          </el-select>
        </el-form-item>
        <el-form-item label="用量">
          <el-input v-model="form.usage_quantity" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="form.usage_unit" />
        </el-form-item>
        <el-form-item label="单价">
          <el-input v-model="form.unit_price" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <div class="dist-head">
        <span>费用归属 / 分摊</span>
        <div>
          <el-button text type="primary" @click="suggestFromResource">按资源分配建议</el-button>
          <el-button text type="primary" @click="addDistRow">增加一行</el-button>
        </div>
      </div>
      <p class="field-hint" :class="{ 'is-error': errors.targets === '项目 / 人员至少选择一项' }">
        项目 / 人员至少选择一项
      </p>
      <p v-if="errors.targets && errors.targets !== '项目 / 人员至少选择一项'" class="field-error">
        {{ errors.targets }}
      </p>
      <div class="list-panel">
        <el-table :data="distRows" empty-text="请添加归属">
          <el-table-column label="项目" min-width="140">
            <template #default="{ row }">
              <el-select v-model="row.project_id" clearable filterable style="width: 100%">
                <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="成员" min-width="140">
            <template #default="{ row }">
              <el-select v-model="row.employee_id" clearable filterable style="width: 100%">
                <el-option
                  v-for="item in employees"
                  :key="item.id"
                  :label="`${item.name} (${item.employee_no})`"
                  :value="item.id"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="方式" width="120">
            <template #default="{ row }">
              <el-select v-model="row.allocation_method" style="width: 100%">
                <el-option v-for="item in methodOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="比例" width="90">
            <template #default="{ row }"><el-input v-model="row.allocation_ratio" /></template>
          </el-table-column>
          <el-table-column label="分摊金额" width="120">
            <template #default="{ row }"><el-input v-model="row.allocated_amount" /></template>
          </el-table-column>
          <el-table-column label="" width="70">
            <template #default="{ $index }">
              <el-button text type="danger" @click="removeDistRow($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <p class="dist-sum">
        分摊合计 {{ distributionSum.toFixed(2) }}
        / 费用金额 {{ form.amount || "-" }}
        {{ distributionMatches ? "（已对齐）" : "（需等于总金额）" }}
      </p>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="typeDialogVisible" title="费用类型" width="720px">
      <el-form label-width="80px">
        <StableIdentifierField
          v-model="typeForm.code"
          label="编码"
          :required="!editingTypeId"
          :locked="Boolean(editingTypeId)"
          :maxlength="50"
          helper="稳定业务标识，普通编辑不可修改。"
          action-label="修正编码"
          :show-action="auth.role === 'ADMIN'"
          @correct="openCodeCorrection"
        />
        <el-form-item label="名称">
          <el-input v-model="typeForm.name" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="typeForm.category" style="width: 100%">
            <el-option v-for="item in categoryOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="typeForm.description" />
        </el-form-item>
      </el-form>
      <div class="list-panel">
        <el-table :data="expenseTypes" empty-text="暂无类型">
          <el-table-column prop="code" label="编码" width="140" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="category" label="类别" width="140" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">{{ row.is_active ? "启用" : "停用" }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button text type="primary" @click="editType(row)">编辑</el-button>
              <el-button text type="primary" @click="toggleType(row)">
                {{ row.is_active ? "停用" : "启用" }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="typeDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="saveType">{{ editingTypeId ? "保存类型" : "新建类型" }}</el-button>
      </template>
    </el-dialog>

    <StableIdentifierCorrectionDialog
      v-model="codeDialogVisible"
      title="修正编码"
      :impact-url="editingTypeId ? `/api/expense-types/${editingTypeId}/code/impact` : ''"
      subject-label="费用类型"
      :subject-value="typeForm.name"
      current-label="当前编码"
      :current-value="typeForm.code"
      new-label="新编码"
      notice="编码是稳定业务标识，仅在录入错误时修正。修正不会改变该费用类型的内部 ID 和已有业务关联。"
      blank-message="请填写新编码"
      same-message="新编码与当前编码一致"
      :submitting="correctingCode"
      :error="codeError"
      @confirm="submitCodeCorrection"
    />
  </section>
</template>

<style scoped>
.dist-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 0 var(--space-2);
  color: var(--color-text-primary);
  font-size: 16px;
}

.dist-sum {
  margin: var(--space-3) 0 0;
  color: var(--color-text-secondary);
  font-size: 14px;
  font-variant-numeric: tabular-nums;
}
</style>
