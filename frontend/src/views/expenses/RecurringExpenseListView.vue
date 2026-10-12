<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { listEmployees, type Employee } from "../../api/employees";
import { listProjects, type Project } from "../../api/projects";
import { listResources, type Resource } from "../../api/resources";
import {
  createRecurringRule,
  disableRecurringRule,
  enableRecurringRule,
  generateRecurringExpenses,
  listExpenseTypes,
  listRecurringRules,
  updateRecurringRule,
  type ExpenseDistributionInput,
  type ExpenseType,
  type RecurringRule,
} from "../../api/expenses";
import { useAuthStore } from "../../stores/auth";
import PageHeader from "../../components/PageHeader.vue";
import { currencyLabel } from "../../utils/money";

type DistRow = {
  project_id?: number;
  employee_id?: number;
  allocation_method: string;
  allocation_ratio: string;
  allocated_amount: string;
};

const auth = useAuthStore();
const loading = ref(false);
const rows = ref<RecurringRule[]>([]);
const expenseTypes = ref<ExpenseType[]>([]);
const projects = ref<Project[]>([]);
const employees = ref<Employee[]>([]);
const resources = ref<Resource[]>([]);
const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const form = reactive({
  name: "",
  expense_type_id: undefined as number | undefined,
  resource_account_id: undefined as number | undefined,
  frequency: "MONTHLY",
  amount: "",
  currency: "CNY",
  start_date: "",
  end_date: "",
  next_run_date: "",
  default_distribution_mode: "DIRECT",
  description: "",
});
const distRows = ref<DistRow[]>([emptyDist()]);

const frequencyOptions = [
  { value: "MONTHLY", label: "月" },
  { value: "QUARTERLY", label: "季度" },
  { value: "YEARLY", label: "年" },
];
const methodOptions = [
  { value: "DIRECT", label: "直接归属" },
  { value: "EQUAL", label: "平均" },
  { value: "RATIO", label: "比例" },
  { value: "MANUAL", label: "手工金额" },
];

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

async function load() {
  loading.value = true;
  try {
    rows.value = await listRecurringRules({ include_inactive: auth.canWriteExpenses });
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editingId.value = null;
  form.name = "";
  form.expense_type_id = undefined;
  form.resource_account_id = undefined;
  form.frequency = "MONTHLY";
  form.amount = "";
  form.currency = "CNY";
  form.start_date = "";
  form.end_date = "";
  form.next_run_date = "";
  form.default_distribution_mode = "DIRECT";
  form.description = "";
  distRows.value = [emptyDist()];
  dialogVisible.value = true;
}

function openEdit(row: RecurringRule) {
  editingId.value = row.id;
  form.name = row.name;
  form.expense_type_id = row.expense_type.id;
  form.resource_account_id = row.resource_account_id ?? undefined;
  form.frequency = row.frequency;
  form.amount = row.amount;
  form.currency = row.currency;
  form.start_date = row.start_date;
  form.end_date = row.end_date || "";
  form.next_run_date = row.next_run_date;
  form.default_distribution_mode = row.default_distribution_mode;
  form.description = row.description || "";
  distRows.value = row.distributions.map((item) => ({
    project_id: item.project_id ?? undefined,
    employee_id: item.employee_id ?? undefined,
    allocation_method: item.allocation_method,
    allocation_ratio: item.allocation_ratio || "",
    allocated_amount: item.allocated_amount || "",
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

function toDistributions(): ExpenseDistributionInput[] {
  return distRows.value.map((row) => ({
    project_id: row.project_id ?? null,
    employee_id: row.employee_id ?? null,
    allocation_method: row.allocation_method,
    allocation_ratio: row.allocation_ratio || null,
    allocated_amount: row.allocated_amount || null,
  }));
}

async function save() {
  if (!form.name || !form.expense_type_id || !form.amount || !form.start_date) {
    ElMessage.warning("请填写规则名称、费用类型、金额和开始日期");
    return;
  }
  const payload = {
    name: form.name,
    expense_type_id: form.expense_type_id,
    resource_account_id: form.resource_account_id ?? null,
    frequency: form.frequency,
    amount: form.amount,
    currency: form.currency,
    start_date: form.start_date,
    end_date: form.end_date || null,
    next_run_date: form.next_run_date || null,
    default_distribution_mode: form.default_distribution_mode,
    description: form.description,
    distributions: toDistributions(),
  };
  if (editingId.value) {
    await updateRecurringRule(editingId.value, payload);
    ElMessage.success("已保存");
  } else {
    await createRecurringRule(payload);
    ElMessage.success("已新增");
  }
  dialogVisible.value = false;
  await load();
}

async function toggle(row: RecurringRule) {
  if (row.is_active) await disableRecurringRule(row.id);
  else await enableRecurringRule(row.id);
  await load();
}

async function generate() {
  const result = await generateRecurringExpenses();
  ElMessage.success(`生成 ${result.generated_count} 条，跳过 ${result.skipped_count} 条`);
  await load();
}

onMounted(async () => {
  expenseTypes.value = await listExpenseTypes({ include_inactive: false });
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
    <PageHeader title="周期规则" description="按月 / 季度 / 年生成费用。重复执行不会重复出账。">
      <template v-if="auth.canWriteExpenses" #actions>
        <el-button @click="generate">生成周期费用</el-button>
        <el-button type="primary" @click="openCreate">新增规则</el-button>
      </template>
    </PageHeader>

    <div class="list-panel">
      <el-table :data="rows" v-loading="loading" empty-text="暂无周期规则">
        <el-table-column prop="name" label="规则名称" min-width="160" />
        <el-table-column label="费用类型" min-width="140">
          <template #default="{ row }">{{ row.expense_type.name }}</template>
        </el-table-column>
        <el-table-column label="资源" min-width="140">
          <template #default="{ row }">{{ row.resource_name || "-" }}</template>
        </el-table-column>
        <el-table-column label="频率" width="90">
          <template #default="{ row }">
            {{ frequencyOptions.find((item) => item.value === row.frequency)?.label || row.frequency }}
          </template>
        </el-table-column>
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }">
            <span class="amount-cell">{{ row.amount }}</span>
          </template>
        </el-table-column>
        <el-table-column label="币种" width="88"><template #default="{ row }">{{ currencyLabel(row.currency) }}</template></el-table-column>
        <el-table-column label="下次生成" width="120">
          <template #default="{ row }">{{ formatDate(row.next_run_date) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">{{ row.is_active ? "启用" : "停用" }}</template>
        </el-table-column>
        <el-table-column v-if="auth.canWriteExpenses" label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button text type="primary" @click="toggle(row)">
              {{ row.is_active ? "停用" : "启用" }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑周期规则' : '新增周期规则'" width="760px">
      <el-form label-width="108px">
        <el-form-item label="规则名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="费用类型">
          <el-select v-model="form.expense_type_id" filterable style="width: 100%">
            <el-option
              v-for="item in expenseTypes"
              :key="item.id"
              :label="`${item.name} (${item.code})`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="资源账号">
          <el-select v-model="form.resource_account_id" clearable filterable style="width: 100%">
            <el-option v-for="item in resources" :key="item.id" :label="item.resource_name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="频率">
          <el-select v-model="form.frequency" style="width: 100%">
            <el-option v-for="item in frequencyOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额">
          <el-input v-model="form.amount" />
        </el-form-item>
        <el-form-item label="币种">
          <el-select v-model="form.currency" style="width: 100%">
            <el-option label="人民币" value="CNY" />
            <el-option label="美元" value="USD" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="下次生成">
          <el-date-picker v-model="form.next_run_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="默认分摊">
          <el-select v-model="form.default_distribution_mode" style="width: 100%">
            <el-option v-for="item in methodOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" />
        </el-form-item>
      </el-form>
      <div class="dist-head">
        <span>分摊模板</span>
        <el-button text type="primary" @click="addDistRow">增加一行</el-button>
      </div>
      <div class="list-panel">
        <el-table :data="distRows" empty-text="请添加分摊模板">
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
          <el-table-column label="金额" width="120">
            <template #default="{ row }"><el-input v-model="row.allocated_amount" /></template>
          </el-table-column>
          <el-table-column width="70">
            <template #default="{ $index }">
              <el-button text type="danger" @click="removeDistRow($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
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
</style>
