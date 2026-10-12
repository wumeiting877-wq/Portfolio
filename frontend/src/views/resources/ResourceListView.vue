<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { listEmployees, type Employee } from "../../api/employees";
import { listProjects, type Project } from "../../api/projects";
import {
  correctResourceName,
  correctResourceTypeCode,
  createResource,
  createResourceType,
  disableResource,
  disableResourceType,
  enableResource,
  enableResourceType,
  listResourceTypes,
  listResources,
  updateResource,
  updateResourceType,
  type Resource,
  type ResourceType,
} from "../../api/resources";
import { useRouteTitle } from "../../composables/roleUi";
import { useAuthStore } from "../../stores/auth";
import PageHeader from "../../components/PageHeader.vue";
import StableIdentifierCorrectionDialog from "../../components/StableIdentifierCorrectionDialog.vue";
import StableIdentifierField from "../../components/StableIdentifierField.vue";
import StatusTag from "../../components/StatusTag.vue";
import { applyApiFieldErrors, resolveApiError } from "../../utils/apiError";
import { containsCredential, hasText } from "../../utils/formRules";

const auth = useAuthStore();
const pageTitle = useRouteTitle("resources");
const router = useRouter();
const loading = ref(false);
const keyword = ref("");
const typeFilter = ref<number | undefined>(undefined);
const statusFilter = ref("");
const projectFilter = ref<number | undefined>(undefined);
const employeeFilter = ref<number | undefined>(undefined);
const expiringFilter = ref("");
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);
const rows = ref<Resource[]>([]);
const resourceTypes = ref<ResourceType[]>([]);
const projects = ref<Project[]>([]);
const employees = ref<Employee[]>([]);
const dialogVisible = ref(false);
const typeDialogVisible = ref(false);
const editingId = ref<number | null>(null);
const editingTypeId = ref<number | null>(null);
const form = reactive({
  resource_name: "",
  resource_type_id: undefined as number | undefined,
  provider: "",
  account_identifier: "",
  plan_name: "",
  status: "ACTIVE",
  purchased_at: "" as string | null,
  activated_at: "" as string | null,
  expires_at: "" as string | null,
  remark: "",
});
const errors = reactive({
  resource_name: "",
  resource_type_id: "",
  account_identifier: "",
  remark: "",
});
const typeForm = reactive({
  code: "",
  name: "",
  category: "DEVELOPMENT",
  description: "",
});
const codeDialogVisible = ref(false);
const codeTarget = ref<ResourceType | null>(null);
const codeError = ref("");
const correctingCode = ref(false);
const nameDialogVisible = ref(false);
const nameError = ref("");
const correctingName = ref(false);

const statusOptions = [
  { value: "ACTIVE", label: "使用中" },
  { value: "IDLE", label: "闲置" },
  { value: "EXPIRED", label: "已到期" },
  { value: "DISABLED", label: "已停用" },
];

const categoryOptions = [
  { value: "AI", label: "AI" },
  { value: "DEVELOPMENT", label: "开发" },
  { value: "DESIGN", label: "设计" },
  { value: "GIT", label: "Git" },
  { value: "CLOUD_SERVER", label: "云服务器" },
  { value: "DATABASE", label: "数据库" },
  { value: "STORAGE", label: "存储" },
  { value: "API", label: "API" },
  { value: "DOMAIN", label: "域名" },
  { value: "EMAIL", label: "邮箱" },
  { value: "OFFICE", label: "办公" },
  { value: "SAAS", label: "SaaS" },
  { value: "OTHER", label: "其他" },
];

const showEmployeeFilter = computed(() => auth.role !== "MEMBER");

function formatDate(value: string | null) {
  return value ? value.slice(0, 10) : "-";
}

function usageText(row: Resource) {
  if (!row.usage_projects.length) return "-";
  return row.usage_projects.map((item) => item.name).join("、");
}

async function loadTypes() {
  resourceTypes.value = await listResourceTypes({
    include_inactive: auth.canWriteResources,
  });
}

async function load() {
  loading.value = true;
  try {
    const result = await listResources({
      keyword: keyword.value || undefined,
      resource_type_id: typeFilter.value,
      status: statusFilter.value || undefined,
      project_id: projectFilter.value,
      employee_id: showEmployeeFilter.value ? employeeFilter.value : undefined,
      expiring_soon: expiringFilter.value === "soon" ? true : undefined,
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
  statusFilter.value = "";
  projectFilter.value = undefined;
  employeeFilter.value = undefined;
  expiringFilter.value = "";
  page.value = 1;
  void load();
}

function clearErrors() {
  errors.resource_name = "";
  errors.resource_type_id = "";
  errors.account_identifier = "";
  errors.remark = "";
}

function openCreate() {
  editingId.value = null;
  clearErrors();
  Object.assign(form, {
    resource_name: "",
    resource_type_id: undefined,
    provider: "",
    account_identifier: "",
    plan_name: "",
    status: "ACTIVE",
    purchased_at: "",
    activated_at: "",
    expires_at: "",
    remark: "",
  });
  dialogVisible.value = true;
}

function openEdit(row: Resource) {
  editingId.value = row.id;
  clearErrors();
  Object.assign(form, {
    resource_name: row.resource_name,
    resource_type_id: row.resource_type.id,
    provider: row.provider || "",
    account_identifier: row.account_identifier || "",
    plan_name: row.plan_name || "",
    status: row.status,
    purchased_at: row.purchased_at || "",
    activated_at: row.activated_at || "",
    expires_at: row.expires_at || "",
    remark: row.remark || "",
  });
  dialogVisible.value = true;
}

function validateForm() {
  clearErrors();
  if (!editingId.value && !hasText(form.resource_name)) errors.resource_name = "请输入资源名称";
  if (!form.resource_type_id) errors.resource_type_id = "请选择资源类型";
  if (containsCredential(form.account_identifier)) errors.account_identifier = "账号标识不能填写凭据";
  if (containsCredential(form.remark)) errors.remark = "备注不能填写凭据";
  return !errors.resource_name && !errors.resource_type_id && !errors.account_identifier && !errors.remark;
}

async function save() {
  if (!validateForm() || !form.resource_type_id) return;
  const resourceName = form.resource_name.trim();
  const shared = {
    resource_type_id: form.resource_type_id,
    provider: form.provider,
    account_identifier: form.account_identifier,
    plan_name: form.plan_name,
    status: form.status,
    purchased_at: form.purchased_at || null,
    activated_at: form.activated_at || null,
    expires_at: form.expires_at || null,
    remark: form.remark,
  };
  if (!editingId.value) {
    try {
      const existing = await listResources({ keyword: resourceName, page: 1, page_size: 100 });
      const duplicated = existing.items.some((item) => item.resource_name === resourceName);
      if (duplicated) {
        errors.resource_name = "资源名称已存在";
        return;
      }
    } catch (error: unknown) {
      applyApiFieldErrors(error, errors);
      return;
    }
  }
  try {
    if (editingId.value) {
      await updateResource(editingId.value, shared);
      ElMessage.success("已保存");
    } else {
      await createResource({ ...shared, resource_name: resourceName });
      ElMessage.success("已创建");
    }
  } catch (error: unknown) {
    applyApiFieldErrors(error, errors);
    return;
  }
  dialogVisible.value = false;
  await load();
}

async function toggleStatus(row: Resource) {
  if (row.status === "DISABLED") {
    await enableResource(row.id);
    ElMessage.success("已启用");
  } else {
    await ElMessageBox.confirm(`确认停用资源 ${row.resource_name}？`, "停用资源", { type: "warning" });
    await disableResource(row.id);
    ElMessage.success("已停用");
  }
  await load();
}

function goDetail(row: Resource, tab?: string) {
  void router.push({
    name: "resource-detail",
    params: { id: String(row.id) },
    query: tab ? { tab } : undefined,
  });
}

function openTypeManager() {
  editingTypeId.value = null;
  Object.assign(typeForm, { code: "", name: "", category: "DEVELOPMENT", description: "" });
  typeDialogVisible.value = true;
  void loadTypes();
}

function editType(row: ResourceType) {
  editingTypeId.value = row.id;
  Object.assign(typeForm, {
    code: row.code,
    name: row.name,
    category: row.category,
    description: row.description || "",
  });
}

function openCodeCorrection() {
  if (auth.role !== "ADMIN" || !editingTypeId.value) return;
  const current = resourceTypes.value.find((item) => item.id === editingTypeId.value);
  if (!current) return;
  codeTarget.value = current;
  codeError.value = "";
  codeDialogVisible.value = true;
}

async function submitCodeCorrection(nextValue: string) {
  const current = codeTarget.value;
  if (!current || auth.role !== "ADMIN" || correctingCode.value) return;
  codeError.value = "";
  correctingCode.value = true;
  try {
    const updated = await correctResourceTypeCode(current.id, nextValue);
    if (editingTypeId.value === current.id) {
      typeForm.code = updated.code;
    }
    codeTarget.value = { ...current, code: updated.code };
    ElMessage.success("编码已修正");
    codeDialogVisible.value = false;
    await loadTypes();
  } catch (error: unknown) {
    codeError.value = resolveApiError(error).message;
  } finally {
    correctingCode.value = false;
  }
}

function openNameCorrection() {
  if (auth.role !== "ADMIN" || !editingId.value) return;
  nameError.value = "";
  nameDialogVisible.value = true;
}

async function submitNameCorrection(nextValue: string) {
  if (!editingId.value || correctingName.value) return;
  correctingName.value = true;
  nameError.value = "";
  try {
    const updated = await correctResourceName(editingId.value, nextValue);
    form.resource_name = updated.resource_name;
    ElMessage.success("资源名称已修正");
    nameDialogVisible.value = false;
    await load();
  } catch (error: unknown) {
    nameError.value = resolveApiError(error).message;
  } finally {
    correctingName.value = false;
  }
}

async function saveType() {
  if (!typeForm.name.trim() || (!editingTypeId.value && !typeForm.code.trim())) {
    ElMessage.warning(editingTypeId.value ? "请填写类型名称" : "请填写类型编码和名称");
    return;
  }
  if (editingTypeId.value) {
    await updateResourceType(editingTypeId.value, {
      name: typeForm.name,
      category: typeForm.category,
      description: typeForm.description,
    });
    ElMessage.success("类型已保存");
  } else {
    await createResourceType({
      code: typeForm.code,
      name: typeForm.name,
      category: typeForm.category,
      description: typeForm.description,
    });
    ElMessage.success("类型已创建");
  }
  editingTypeId.value = null;
  Object.assign(typeForm, { code: "", name: "", category: "DEVELOPMENT", description: "" });
  await loadTypes();
}

async function toggleType(row: ResourceType) {
  if (row.is_active) {
    await disableResourceType(row.id);
  } else {
    await enableResourceType(row.id);
  }
  await loadTypes();
}

onMounted(async () => {
  await loadTypes();
  projects.value = (await listProjects({ page: 1, page_size: 100 })).items;
  if (auth.canViewEmployees) {
    employees.value = await listEmployees({ employment_status: "ACTIVE" });
  }
  await load();
});
</script>

<template>
  <section class="list-page">
    <PageHeader :title="pageTitle" description="查看企业采购资源及其项目和成员分配情况">
      <template v-if="auth.canWriteResources" #actions>
        <el-button @click="openTypeManager">资源类型</el-button>
        <el-button type="primary" @click="openCreate">新建资源</el-button>
      </template>
    </PageHeader>

    <div class="list-toolbar">
      <el-input
        v-model="keyword"
        class="list-toolbar__search"
        placeholder="资源名称、平台或标识"
        @keyup.enter="load"
      />
      <el-select v-model="typeFilter" clearable placeholder="资源类型" class="list-toolbar__status">
        <el-option
          v-for="item in resourceTypes.filter((type) => type.is_active)"
          :key="item.id"
          :label="item.name"
          :value="item.id"
        />
      </el-select>
      <el-select v-model="statusFilter" clearable placeholder="状态" class="list-toolbar__status">
        <el-option
          v-for="item in statusOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-select v-model="projectFilter" clearable filterable placeholder="项目" class="list-toolbar__status">
        <el-option
          v-for="item in projects"
          :key="item.id"
          :label="item.name"
          :value="item.id"
        />
      </el-select>
      <el-select
        v-if="showEmployeeFilter && auth.canViewEmployees"
        v-model="employeeFilter"
        clearable
        filterable
        placeholder="使用人"
        class="list-toolbar__status"
      >
        <el-option
          v-for="item in employees"
          :key="item.id"
          :label="`${item.name} (${item.employee_no})`"
          :value="item.id"
        />
      </el-select>
      <el-select v-model="expiringFilter" clearable placeholder="到期状态" class="list-toolbar__status">
        <el-option label="即将到期" value="soon" />
      </el-select>
      <el-button @click="load">查询</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <div class="list-panel">
      <el-table :data="rows" v-loading="loading" empty-text="暂无数据">
        <el-table-column prop="resource_name" label="资源名称" min-width="160" />
        <el-table-column label="类型" width="120">
          <template #default="{ row }">{{ row.resource_type.name }}</template>
        </el-table-column>
        <el-table-column prop="provider" label="平台" width="120">
          <template #default="{ row }">{{ row.provider || "-" }}</template>
        </el-table-column>
        <el-table-column label="账号/标识" min-width="160">
          <template #default="{ row }">{{ row.account_identifier || "-" }}</template>
        </el-table-column>
        <el-table-column label="套餐" width="110">
          <template #default="{ row }">{{ row.plan_name || "-" }}</template>
        </el-table-column>
        <el-table-column label="使用项目" min-width="140">
          <template #default="{ row }">{{ usageText(row) }}</template>
        </el-table-column>
        <el-table-column prop="active_user_count" label="使用人数" width="88" />
        <el-table-column label="状态" width="130">
          <template #default="{ row }">
            <StatusTag kind="resource" :code="row.status" />
            <StatusTag v-if="row.is_expiring_soon" kind="resource" code="EXPIRING_SOON" />
          </template>
        </el-table-column>
        <el-table-column label="到期时间" width="120">
          <template #default="{ row }">{{ formatDate(row.expires_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" :width="auth.canWriteResources ? 220 : 88" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="goDetail(row)">查看</el-button>
            <template v-if="auth.canWriteResources">
              <el-button text type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button text type="primary" @click="goDetail(row, 'allocations')">分配</el-button>
              <el-button text :type="row.status === 'DISABLED' ? 'primary' : 'danger'" @click="toggleStatus(row)">
                {{ row.status === "DISABLED" ? "启用" : "停用" }}
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑资源' : '新建资源'" width="560px">
      <el-form class="ibm-form" label-width="96px">
        <StableIdentifierField
          v-model="form.resource_name"
          label="资源名称"
          required
          :locked="Boolean(editingId)"
          :maxlength="200"
          :error="errors.resource_name"
          helper="稳定业务标识，普通编辑不可修改。"
          action-label="修正资源名称"
          :show-action="auth.role === 'ADMIN'"
          @correct="openNameCorrection"
        />
        <el-form-item :error="errors.resource_type_id">
          <template #label>资源类型<span class="field-required">*</span></template>
          <el-select v-model="form.resource_type_id" filterable style="width: 100%">
            <el-option
              v-for="item in resourceTypes"
              :key="item.id"
              :label="item.is_active ? `${item.name} (${item.code})` : `${item.name} (${item.code}) · 已停用`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="平台">
          <el-input v-model="form.provider" />
        </el-form-item>
        <el-form-item label="账号/标识" :error="errors.account_identifier">
          <el-input v-model="form.account_identifier" />
        </el-form-item>
        <el-form-item label="套餐">
          <el-input v-model="form.plan_name" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option
              v-for="item in statusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="购买日期">
          <el-date-picker v-model="form.purchased_at" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="启用日期">
          <el-date-picker v-model="form.activated_at" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="到期日期">
          <el-date-picker v-model="form.expires_at" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注" :error="errors.remark">
          <el-input v-model="form.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="typeDialogVisible" title="资源类型" width="720px">
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
            <el-option
              v-for="item in categoryOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="typeForm.description" />
        </el-form-item>
      </el-form>
      <div class="list-panel">
        <el-table :data="resourceTypes" empty-text="暂无类型">
          <el-table-column prop="code" label="编码" width="140" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="category" label="类别" width="120" />
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
      :impact-url="codeTarget ? `/api/resource-types/${codeTarget.id}/code/impact` : ''"
      subject-label="资源类型"
      :subject-value="codeTarget?.name || ''"
      current-label="当前编码"
      :current-value="codeTarget?.code || ''"
      new-label="新编码"
      notice="编码是稳定业务标识，仅在录入错误时修正。修正不会改变该资源类型的内部 ID 和已有业务关联。"
      blank-message="请填写新编码"
      same-message="新编码与当前编码一致"
      :submitting="correctingCode"
      :error="codeError"
      @confirm="submitCodeCorrection"
    />
    <StableIdentifierCorrectionDialog
      v-model="nameDialogVisible"
      title="修正资源名称"
      :impact-url="editingId ? `/api/resources/${editingId}/resource-name/impact` : ''"
      current-label="当前资源名称"
      :current-value="form.resource_name"
      new-label="新资源名称"
      notice="资源名称是稳定业务标识，仅在录入错误时修正。修正不会改变该资源的内部 ID 和已有业务关联。"
      blank-message="请填写新资源名称"
      same-message="新资源名称与当前资源名称一致"
      :submitting="correctingName"
      :error="nameError"
      @confirm="submitNameCorrection"
    />
  </section>
</template>
