<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { listEmployees, type Employee } from "../../api/employees";
import { listProjects, type Project } from "../../api/projects";
import { applyApiFieldErrors } from "../../utils/apiError";
import {
  addResourceAllocation,
  getResource,
  listResourceAllocations,
  releaseResourceAllocation,
  restoreResourceAllocation,
  type Resource,
  type ResourceAllocation,
} from "../../api/resources";
import { listExpenses, type Expense } from "../../api/expenses";
import { useDynamicBreadcrumbTitle } from "../../composables/breadcrumb";
import { useAuthStore } from "../../stores/auth";
import PageHeader from "../../components/PageHeader.vue";
import StatusTag from "../../components/StatusTag.vue";
import { currencyLabel } from "../../utils/money";

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();
const loading = ref(false);
const resource = ref<Resource | null>(null);
const allocations = ref<ResourceAllocation[]>([]);
const expenses = ref<Expense[]>([]);
const projects = ref<Project[]>([]);
const employees = ref<Employee[]>([]);
const dialogVisible = ref(false);
const tab = ref(
  route.query.tab === "allocations" ? "allocations" : route.query.tab === "expenses" ? "expenses" : "overview",
);
const form = reactive({
  project_id: undefined as number | undefined,
  employee_id: undefined as number | undefined,
  remark: "",
});
const errors = reactive({
  resource: "",
  targets: "",
});

const resourceId = computed(() => Number(route.params.id));

useDynamicBreadcrumbTitle(() => resource.value?.resource_name ?? null);

function formatDate(value: string | null) {
  return value ? value.slice(0, 10) : "-";
}

function formatDateTime(value: string | null) {
  if (!value) return "-";
  return value.replace("T", " ").slice(0, 19);
}

async function load() {
  loading.value = true;
  try {
    const [resourceData, allocationData, expenseData] = await Promise.all([
      getResource(resourceId.value),
      listResourceAllocations(resourceId.value),
      listExpenses({ resource_account_id: resourceId.value, page: 1, page_size: 100 }),
    ]);
    resource.value = resourceData;
    allocations.value = allocationData;
    expenses.value = expenseData.items;
  } finally {
    loading.value = false;
  }
}

async function switchTab(next: string) {
  tab.value = next;
  await router.replace({
    name: "resource-detail",
    params: { id: String(resourceId.value) },
    query: next === "overview" ? undefined : { tab: next },
  });
}

function openAllocate() {
  form.project_id = undefined;
  form.employee_id = undefined;
  form.remark = "";
  errors.resource = "";
  errors.targets = "";
  dialogVisible.value = true;
}

async function saveAllocation() {
  errors.resource = "";
  errors.targets = "";
  if (!resource.value) {
    errors.resource = "请选择资源";
    return;
  }
  if (!form.project_id && !form.employee_id) {
    errors.targets = "项目和人员至少选择一项";
    return;
  }
  try {
    await addResourceAllocation(resourceId.value, {
      project_id: form.project_id ?? null,
      employee_id: form.employee_id ?? null,
      remark: form.remark,
    });
  } catch (error: unknown) {
    applyApiFieldErrors(error, errors);
    return;
  }
  ElMessage.success("已分配");
  dialogVisible.value = false;
  await load();
}

async function release(row: ResourceAllocation) {
  await ElMessageBox.confirm("确认释放该分配？不会物理删除记录。", "释放分配", { type: "warning" });
  await releaseResourceAllocation(resourceId.value, row.id);
  ElMessage.success("已释放");
  await load();
}

async function restore(row: ResourceAllocation) {
  await restoreResourceAllocation(resourceId.value, row.id);
  ElMessage.success("已恢复");
  await load();
}

watch(
  () => route.query.tab,
  (value) => {
    tab.value =
      value === "allocations" ? "allocations" : value === "expenses" ? "expenses" : "overview";
  },
);

onMounted(async () => {
  if (auth.canWriteResources) {
    projects.value = (await listProjects({ page: 1, page_size: 100 })).items;
    employees.value = await listEmployees({ employment_status: "ACTIVE" });
  }
  await load();
});
</script>

<template>
  <section class="list-page" v-loading="loading">
    <PageHeader :title="resource?.resource_name || '资源详情'" :description="resource?.resource_type.name">
      <template #actions>
        <el-button @click="router.push({ name: 'resources' })">返回列表</el-button>
        <el-button v-if="auth.canWriteResources && tab === 'allocations'" type="primary" @click="openAllocate">
          新增分配
        </el-button>
      </template>
    </PageHeader>

    <div class="product-tabs">
      <button class="product-tab" :class="{ 'is-selected': tab === 'overview' }" type="button" @click="switchTab('overview')">
        概览
      </button>
      <button
        class="product-tab"
        :class="{ 'is-selected': tab === 'allocations' }"
        type="button"
        @click="switchTab('allocations')"
      >
        分配记录
      </button>
      <button
        class="product-tab"
        :class="{ 'is-selected': tab === 'expenses' }"
        type="button"
        @click="switchTab('expenses')"
      >
        费用记录
      </button>
    </div>

    <el-descriptions v-if="tab === 'overview' && resource" class="home-facts" :column="2" border>
      <el-descriptions-item label="资源名称">{{ resource.resource_name }}</el-descriptions-item>
      <el-descriptions-item label="资源类型">
        {{ resource.resource_type.name }} ({{ resource.resource_type.code }})
      </el-descriptions-item>
      <el-descriptions-item label="平台">{{ resource.provider || "-" }}</el-descriptions-item>
      <el-descriptions-item label="账号标识">{{ resource.account_identifier || "-" }}</el-descriptions-item>
      <el-descriptions-item label="套餐">{{ resource.plan_name || "-" }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <StatusTag kind="resource" :code="resource.status" />
        <StatusTag v-if="resource.is_expiring_soon" kind="resource" code="EXPIRING_SOON" />
      </el-descriptions-item>
      <el-descriptions-item label="购买日期">{{ formatDate(resource.purchased_at) }}</el-descriptions-item>
      <el-descriptions-item label="启用日期">{{ formatDate(resource.activated_at) }}</el-descriptions-item>
      <el-descriptions-item label="到期日期">{{ formatDate(resource.expires_at) }}</el-descriptions-item>
      <el-descriptions-item label="即将到期">{{ resource.is_expiring_soon ? "是" : "否" }}</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ formatDateTime(resource.created_at) }}</el-descriptions-item>
      <el-descriptions-item label="更新时间">{{ formatDateTime(resource.updated_at) }}</el-descriptions-item>
      <el-descriptions-item label="备注" :span="2">{{ resource.remark || "-" }}</el-descriptions-item>
    </el-descriptions>

    <div v-if="tab === 'allocations'" class="list-panel">
      <el-table :data="allocations" empty-text="暂无分配记录">
        <el-table-column label="项目" min-width="160">
          <template #default="{ row }">{{ row.project_name || "-" }}</template>
        </el-table-column>
        <el-table-column label="使用人" width="160">
          <template #default="{ row }">{{ row.employee_name || "-" }}</template>
        </el-table-column>
        <el-table-column label="分配时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.allocated_at) }}</template>
        </el-table-column>
        <el-table-column label="释放时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.released_at) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <StatusTag kind="allocation" :code="row.is_active ? 'ACTIVE' : 'INACTIVE'" />
          </template>
        </el-table-column>
        <el-table-column v-if="auth.canWriteResources" label="操作" width="140">
          <template #default="{ row }">
            <el-button v-if="row.is_active" text type="danger" @click="release(row)">释放</el-button>
            <el-button v-else text type="primary" @click="restore(row)">恢复</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div v-if="tab === 'expenses'" class="list-panel">
      <el-table :data="expenses" empty-text="暂无费用记录">
        <el-table-column label="费用日期" width="120">
          <template #default="{ row }">{{ formatDate(row.expense_date) }}</template>
        </el-table-column>
        <el-table-column label="费用类型" min-width="140">
          <template #default="{ row }">{{ row.expense_type.name }}</template>
        </el-table-column>
        <el-table-column label="计费方式" width="100">
          <template #default="{ row }">
            <StatusTag kind="billing" :code="row.billing_mode" />
          </template>
        </el-table-column>
        <el-table-column label="可见归属" min-width="160">
          <template #default="{ row }">{{ row.visible_attribution || "-" }}</template>
        </el-table-column>
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }">
            <span class="amount-cell">{{ row.amount }}</span>
          </template>
        </el-table-column>
        <el-table-column label="币种" width="88"><template #default="{ row }">{{ currencyLabel(row.currency) }}</template></el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <StatusTag kind="expense" :code="row.status" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="88">
          <template #default="{ row }">
            <el-button text type="primary" @click="router.push({ name: 'expense-detail', params: { id: String(row.id) } })">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" title="新增分配" width="480px">
      <el-form class="ibm-form" label-width="80px">
        <el-form-item :error="errors.resource">
          <template #label>资源<span class="field-required">*</span></template>
          <el-input :model-value="resource?.resource_name || ''" disabled />
        </el-form-item>
        <el-form-item label="项目">
          <el-select v-model="form.project_id" clearable filterable style="width: 100%">
            <el-option
              v-for="item in projects"
              :key="item.id"
              :label="`${item.name} (${item.project_code})`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="人员">
          <el-select v-model="form.employee_id" clearable filterable style="width: 100%">
            <el-option
              v-for="item in employees"
              :key="item.id"
              :label="`${item.name} (${item.employee_no})`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <p class="field-hint" :class="{ 'is-error': errors.targets === '项目和人员至少选择一项' }">
          项目和人员至少选择一项
        </p>
        <p v-if="errors.targets && errors.targets !== '项目和人员至少选择一项'" class="field-error">
          {{ errors.targets }}
        </p>
        <el-form-item label="备注">
          <el-input v-model="form.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAllocation">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>
