<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { listEmployees, type Employee } from "../../api/employees";
import {
  archiveProject,
  correctProjectCode,
  createProject,
  listProjects,
  updateProject,
  type Project,
} from "../../api/projects";
import { useRouteTitle } from "../../composables/roleUi";
import { useAuthStore } from "../../stores/auth";
import PageHeader from "../../components/PageHeader.vue";
import StableIdentifierCorrectionDialog from "../../components/StableIdentifierCorrectionDialog.vue";
import StableIdentifierField from "../../components/StableIdentifierField.vue";
import StatusTag from "../../components/StatusTag.vue";
import { applyApiFieldErrors, resolveApiError } from "../../utils/apiError";
import { endBeforeStart, hasText } from "../../utils/formRules";

const auth = useAuthStore();
const pageTitle = useRouteTitle("projects");
const router = useRouter();
const loading = ref(false);
const keyword = ref("");
const statusFilter = ref("");
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);
const rows = ref<Project[]>([]);
const employees = ref<Employee[]>([]);
const dialogVisible = ref(false);
const correctionVisible = ref(false);
const correcting = ref(false);
const correctionError = ref("");
const editingId = ref<number | null>(null);
const form = reactive({
  project_code: "",
  name: "",
  manager_employee_id: undefined as number | undefined,
  status: "PLANNING",
  start_date: "" as string | null,
  end_date: "" as string | null,
  description: "",
});
const errors = reactive({
  project_code: "",
  name: "",
  manager_employee_id: "",
  end_date: "",
});

const statusOptions = [
  { value: "PLANNING", label: "筹备中" },
  { value: "ACTIVE", label: "进行中" },
  { value: "PAUSED", label: "已暂停" },
  { value: "COMPLETED", label: "已完成" },
  { value: "ARCHIVED", label: "已归档" },
];

function formatDate(value: string | null) {
  return value ? value.slice(0, 10) : "-";
}

function formatDateTime(value: string) {
  return value.replace("T", " ").slice(0, 19);
}

async function load() {
  loading.value = true;
  try {
    const result = await listProjects({
      keyword: keyword.value || undefined,
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
  statusFilter.value = "";
  page.value = 1;
  void load();
}

function clearErrors() {
  errors.project_code = "";
  errors.name = "";
  errors.manager_employee_id = "";
  errors.end_date = "";
}

function openCreate() {
  editingId.value = null;
  clearErrors();
  Object.assign(form, {
    project_code: "",
    name: "",
    manager_employee_id: undefined,
    status: "PLANNING",
    start_date: "",
    end_date: "",
    description: "",
  });
  dialogVisible.value = true;
}

function openEdit(row: Project) {
  editingId.value = row.id;
  clearErrors();
  Object.assign(form, {
    project_code: row.project_code,
    name: row.name,
    manager_employee_id: row.manager_employee_id,
    status: row.status === "ARCHIVED" ? "ARCHIVED" : row.status,
    start_date: row.start_date || "",
    end_date: row.end_date || "",
    description: row.description || "",
  });
  dialogVisible.value = true;
}

function openCorrection() {
  if (auth.role !== "ADMIN" || !editingId.value) return;
  correctionError.value = "";
  correctionVisible.value = true;
}

async function submitCorrection(nextValue: string) {
  if (!editingId.value || correcting.value) return;
  correcting.value = true;
  correctionError.value = "";
  try {
    const updated = await correctProjectCode(editingId.value, nextValue);
    form.project_code = updated.project_code;
    correctionVisible.value = false;
    ElMessage.success("项目编码已修正");
    await load();
  } catch (error: unknown) {
    correctionError.value = resolveApiError(error).message;
  } finally {
    correcting.value = false;
  }
}

function validateForm() {
  clearErrors();
  if (!editingId.value && !hasText(form.project_code)) errors.project_code = "请输入项目编码";
  if (!hasText(form.name)) errors.name = "请输入项目名称";
  if (!form.manager_employee_id) errors.manager_employee_id = "请选择项目负责人";
  if (endBeforeStart(form.start_date, form.end_date)) errors.end_date = "结束日期不能早于开始日期";
  return !errors.project_code && !errors.name && !errors.manager_employee_id && !errors.end_date;
}

async function save() {
  if (!validateForm() || !form.manager_employee_id) return;
  const payload = {
    project_code: form.project_code.trim(),
    name: form.name.trim(),
    manager_employee_id: form.manager_employee_id,
    status: form.status,
    start_date: form.start_date || null,
    end_date: form.end_date || null,
    description: form.description,
  };
  try {
    if (editingId.value) {
      const { project_code: _code, ...updatePayload } = payload;
      if (updatePayload.status === "ARCHIVED") {
        delete (updatePayload as { status?: string }).status;
      }
      await updateProject(editingId.value, updatePayload);
      ElMessage.success("已保存");
    } else {
      await createProject(payload);
      ElMessage.success("已创建");
    }
  } catch (error: unknown) {
    applyApiFieldErrors(error, errors);
    return;
  }
  dialogVisible.value = false;
  await load();
}

async function archive(row: Project) {
  await ElMessageBox.confirm(`确认归档项目 ${row.name}？归档后不再物理删除。`, "归档项目", {
    type: "warning",
  });
  await archiveProject(row.id);
  ElMessage.success("已归档");
  await load();
}

function goDetail(row: Project, tab?: string) {
  void router.push({
    name: "project-detail",
    params: { id: String(row.id) },
    query: tab ? { tab } : undefined,
  });
}

onMounted(async () => {
  if (auth.canWriteProjects) {
    employees.value = await listEmployees();
  }
  await load();
});
</script>

<template>
  <section class="list-page">
    <PageHeader :title="pageTitle" description="按当前账号数据范围查看可访问的项目。">
      <template v-if="auth.canWriteProjects" #actions>
        <el-button type="primary" @click="openCreate">新建项目</el-button>
      </template>
    </PageHeader>

    <div class="list-toolbar">
      <el-input
        v-model="keyword"
        class="list-toolbar__search"
        placeholder="项目名称或编码"
        @keyup.enter="load"
      />
      <el-select v-model="statusFilter" clearable placeholder="状态" class="list-toolbar__status">
        <el-option
          v-for="item in statusOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-button @click="load">查询</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <div class="list-panel">
      <el-table :data="rows" v-loading="loading" empty-text="暂无数据">
        <el-table-column prop="project_code" label="项目编码" width="140" />
        <el-table-column prop="name" label="项目名称" min-width="160" />
        <el-table-column label="负责人" width="140">
          <template #default="{ row }">
            {{ row.manager_name || "-" }}
          </template>
        </el-table-column>
        <el-table-column prop="member_count" label="成员数" width="88" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <StatusTag kind="project" :code="row.status" />
          </template>
        </el-table-column>
        <el-table-column label="开始日期" width="120">
          <template #default="{ row }">{{ formatDate(row.start_date) }}</template>
        </el-table-column>
        <el-table-column label="结束日期" width="120">
          <template #default="{ row }">{{ formatDate(row.end_date) }}</template>
        </el-table-column>
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" :width="auth.canWriteProjects ? 220 : 88" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="goDetail(row)">查看</el-button>
            <template v-if="auth.canWriteProjects">
              <el-button text type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button text type="primary" @click="goDetail(row, 'members')">成员</el-button>
              <el-button
                text
                type="danger"
                :disabled="row.status === 'ARCHIVED'"
                @click="archive(row)"
              >
                归档
              </el-button>
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑项目' : '新建项目'" width="560px">
      <el-form class="ibm-form" label-width="120px">
        <StableIdentifierField
          v-model="form.project_code"
          label="项目编码"
          required
          :locked="Boolean(editingId)"
          :maxlength="50"
          :error="errors.project_code"
          helper="稳定业务标识，普通编辑不可修改。"
          action-label="修正项目编码"
          :show-action="auth.role === 'ADMIN'"
          @correct="openCorrection"
        />
        <el-form-item :error="errors.name">
          <template #label>项目名称<span class="field-required">*</span></template>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :error="errors.manager_employee_id">
          <template #label>项目负责人<span class="field-required">*</span></template>
          <el-select v-model="form.manager_employee_id" filterable style="width: 100%">
            <el-option
              v-for="employee in employees"
              :key="employee.id"
              :label="employee.employment_status === 'ACTIVE' ? `${employee.name} (${employee.employee_no})` : `${employee.name} (${employee.employee_no}) · 已停用`"
              :value="employee.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="项目状态">
          <el-select v-model="form.status" style="width: 100%" :disabled="form.status === 'ARCHIVED'">
            <el-option
              v-for="item in statusOptions.filter((option) => option.value !== 'ARCHIVED')"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束日期" :error="errors.end_date">
          <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="项目说明">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <StableIdentifierCorrectionDialog
      v-model="correctionVisible"
      title="修正项目编码"
      :impact-url="editingId ? `/api/projects/${editingId}/project-code/impact` : ''"
      subject-label="项目"
      :subject-value="form.name"
      current-label="当前编码"
      :current-value="form.project_code"
      new-label="新编码"
      notice="项目编码是稳定业务标识，仅在录入错误时修正。修正不会改变该项目的内部 ID 和已有业务关联。"
      blank-message="请填写新编码"
      same-message="新项目编码与当前项目编码一致"
      :submitting="correcting"
      :error="correctionError"
      @confirm="submitCorrection"
    />
  </section>
</template>
