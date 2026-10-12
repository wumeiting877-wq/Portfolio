<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { listEmployees, type Employee } from "../../api/employees";
import {
  addProjectMember,
  getProject,
  listProjectMembers,
  removeProjectMember,
  type Project,
  type ProjectMember,
} from "../../api/projects";
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
const project = ref<Project | null>(null);
const members = ref<ProjectMember[]>([]);
const expenses = ref<Expense[]>([]);
const employees = ref<Employee[]>([]);
const memberDialogVisible = ref(false);
const selectedEmployeeId = ref<number | undefined>(undefined);
const tab = ref(
  route.query.tab === "members" ? "members" : route.query.tab === "expenses" ? "expenses" : "overview",
);

const projectId = computed(() => Number(route.params.id));

useDynamicBreadcrumbTitle(() => project.value?.name ?? null);

const activeEmployees = computed(() => {
  const activeIds = new Set(
    members.value.filter((item) => item.is_active).map((item) => item.employee_id),
  );
  return employees.value.filter((item) => !activeIds.has(item.id));
});

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
    const [projectData, memberData, expenseData] = await Promise.all([
      getProject(projectId.value),
      listProjectMembers(projectId.value),
      listExpenses({ project_id: projectId.value, page: 1, page_size: 100 }),
    ]);
    project.value = projectData;
    members.value = memberData;
    expenses.value = expenseData.items;
  } finally {
    loading.value = false;
  }
}

async function switchTab(next: string) {
  tab.value = next;
  await router.replace({
    name: "project-detail",
    params: { id: String(projectId.value) },
    query: next === "overview" ? undefined : { tab: next },
  });
  if (next === "members" && members.value.length === 0) {
    members.value = await listProjectMembers(projectId.value);
  }
}

function openAddMember() {
  selectedEmployeeId.value = undefined;
  memberDialogVisible.value = true;
}

async function saveMember() {
  if (!selectedEmployeeId.value) {
    ElMessage.warning("请选择人员");
    return;
  }
  await addProjectMember(projectId.value, { employee_id: selectedEmployeeId.value });
  ElMessage.success("已添加");
  memberDialogVisible.value = false;
  members.value = await listProjectMembers(projectId.value);
  project.value = await getProject(projectId.value);
}

async function removeMember(row: ProjectMember) {
  await ElMessageBox.confirm(`确认移除成员 ${row.name}？`, "移除成员", { type: "warning" });
  await removeProjectMember(projectId.value, row.employee_id);
  ElMessage.success("已移除");
  members.value = await listProjectMembers(projectId.value);
  project.value = await getProject(projectId.value);
}

watch(
  () => route.query.tab,
  (value) => {
    tab.value = value === "members" ? "members" : value === "expenses" ? "expenses" : "overview";
  },
);

onMounted(async () => {
  if (auth.canWriteProjects) {
    employees.value = await listEmployees({ employment_status: "ACTIVE" });
  }
  await load();
});
</script>

<template>
  <section class="list-page" v-loading="loading">
    <PageHeader :title="project?.name || '项目详情'" :description="project?.project_code">
      <template #actions>
        <el-button @click="router.push({ name: 'projects' })">返回列表</el-button>
        <el-button v-if="auth.canWriteProjects && tab === 'members'" type="primary" @click="openAddMember">
          添加成员
        </el-button>
      </template>
    </PageHeader>

    <div class="product-tabs">
      <button class="product-tab" :class="{ 'is-selected': tab === 'overview' }" type="button" @click="switchTab('overview')">
        概览
      </button>
      <button class="product-tab" :class="{ 'is-selected': tab === 'members' }" type="button" @click="switchTab('members')">
        成员
      </button>
      <button class="product-tab" :class="{ 'is-selected': tab === 'expenses' }" type="button" @click="switchTab('expenses')">
        费用
      </button>
    </div>

    <el-descriptions v-if="tab === 'overview' && project" class="home-facts" :column="2" border>
      <el-descriptions-item label="项目名称">{{ project.name }}</el-descriptions-item>
      <el-descriptions-item label="项目编码">{{ project.project_code }}</el-descriptions-item>
      <el-descriptions-item label="负责人">
        {{ project.manager_name ? `${project.manager_name} (${project.manager_employee_no})` : "-" }}
      </el-descriptions-item>
      <el-descriptions-item label="状态">
        <StatusTag kind="project" :code="project.status" />
      </el-descriptions-item>
      <el-descriptions-item label="开始日期">{{ formatDate(project.start_date) }}</el-descriptions-item>
      <el-descriptions-item label="结束日期">{{ formatDate(project.end_date) }}</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ formatDateTime(project.created_at) }}</el-descriptions-item>
      <el-descriptions-item label="更新时间">{{ formatDateTime(project.updated_at) }}</el-descriptions-item>
      <el-descriptions-item label="项目说明" :span="2">
        {{ project.description || "-" }}
      </el-descriptions-item>
    </el-descriptions>

    <div v-if="tab === 'members'" class="list-panel">
      <el-table :data="members" empty-text="暂无成员">
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="employee_no" label="工号" width="140" />
        <el-table-column prop="department" label="部门" />
        <el-table-column prop="position" label="职位" />
        <el-table-column label="成员角色" width="120">
          <template #default="{ row }">
            <StatusTag kind="role" :code="row.member_role" />
          </template>
        </el-table-column>
        <el-table-column label="加入日期" width="180">
          <template #default="{ row }">{{ formatDateTime(row.joined_at) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <StatusTag kind="membership" :code="row.is_active ? 'ACTIVE' : 'INACTIVE'" />
          </template>
        </el-table-column>
        <el-table-column v-if="auth.canWriteProjects" label="操作" width="100">
          <template #default="{ row }">
            <el-button
              text
              type="danger"
              :disabled="!row.is_active || row.employee_id === project?.manager_employee_id"
              @click="removeMember(row)"
            >
              移除
            </el-button>
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
        <el-table-column label="资源" min-width="140">
          <template #default="{ row }">{{ row.resource_name || "-" }}</template>
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

    <el-dialog v-model="memberDialogVisible" title="添加成员" width="480px">
      <el-form label-width="80px">
        <el-form-item label="人员">
          <el-select v-model="selectedEmployeeId" filterable style="width: 100%" placeholder="搜索姓名或工号">
            <el-option
              v-for="employee in activeEmployees"
              :key="employee.id"
              :label="`${employee.name} (${employee.employee_no})`"
              :value="employee.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="memberDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveMember">添加</el-button>
      </template>
    </el-dialog>
  </section>
</template>
