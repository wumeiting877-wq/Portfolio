<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { listEmployees, type Employee } from "../../api/employees";
import {
  correctUsername,
  createUser,
  disableUser,
  enableUser,
  listRoles,
  listUsers,
  resetUserPassword,
  updateUser,
  type Role,
} from "../../api/users";
import type { UserPublic } from "../../api/auth";
import PageHeader from "../../components/PageHeader.vue";
import StableIdentifierCorrectionDialog from "../../components/StableIdentifierCorrectionDialog.vue";
import StableIdentifierField from "../../components/StableIdentifierField.vue";
import StatusTag from "../../components/StatusTag.vue";
import { resolveApiError } from "../../utils/apiError";
import { useAuthStore } from "../../stores/auth";

const ROLE_LABELS: Record<string, string> = {
  ADMIN: "管理员",
  BOSS: "老板",
  PROJECT_MANAGER: "负责人",
  MEMBER: "成员",
};

const auth = useAuthStore();
const loading = ref(false);
const users = ref<UserPublic[]>([]);
const roles = ref<Role[]>([]);
const employees = ref<Employee[]>([]);
const dialogVisible = ref(false);
const editVisible = ref(false);
const resetVisible = ref(false);
const correctionVisible = ref(false);
const correcting = ref(false);
const correctionError = ref("");
const currentUserId = ref<number | null>(null);
const editingUser = ref<UserPublic | null>(null);
const form = reactive({
  username: "",
  password: "",
  role_id: undefined as number | undefined,
  employee_id: undefined as number | undefined,
});
const editForm = reactive({
  username: "",
  role_id: undefined as number | undefined,
  employee_id: undefined as number | undefined,
  status: "ACTIVE",
});
const resetForm = reactive({
  password: "",
});

function roleLabel(role: Role) {
  return ROLE_LABELS[role.code] ?? role.name;
}

async function load() {
  loading.value = true;
  try {
    [users.value, roles.value, employees.value] = await Promise.all([
      listUsers(),
      listRoles(),
      listEmployees(),
    ]);
  } finally {
    loading.value = false;
  }
}

const statusOptions = [
  { value: "ACTIVE", label: "启用" },
  { value: "DISABLED", label: "停用" },
  { value: "LOCKED", label: "锁定" },
];

function openCreate() {
  form.username = "";
  form.password = "";
  form.role_id = roles.value[0]?.id;
  form.employee_id = undefined;
  dialogVisible.value = true;
}

async function save() {
  if (!form.role_id) {
    ElMessage.warning("请选择角色");
    return;
  }
  await createUser({
    username: form.username,
    password: form.password,
    role_id: form.role_id,
    employee_id: form.employee_id,
  });
  ElMessage.success("账号已创建");
  dialogVisible.value = false;
  await load();
}

function openEdit(row: UserPublic) {
  editingUser.value = row;
  editForm.username = row.username;
  editForm.role_id = row.role_id;
  editForm.employee_id = row.employee_id ?? undefined;
  editForm.status = row.status;
  editVisible.value = true;
}

async function saveEdit() {
  if (!editingUser.value || !editForm.role_id) {
    ElMessage.warning("请选择角色");
    return;
  }
  await updateUser(editingUser.value.id, {
    role_id: editForm.role_id,
    status: editForm.status,
    employee_id: editForm.employee_id,
  });
  ElMessage.success("账号已保存");
  editVisible.value = false;
  await load();
}

function openCorrection() {
  if (auth.role !== "ADMIN" || !editingUser.value) return;
  correctionError.value = "";
  correctionVisible.value = true;
}

async function submitCorrection(nextValue: string) {
  if (!editingUser.value || correcting.value) return;
  correcting.value = true;
  correctionError.value = "";
  try {
    const updated = await correctUsername(editingUser.value.id, nextValue);
    editForm.username = updated.username;
    editingUser.value = updated;
    correctionVisible.value = false;
    ElMessage.success("用户名已修正");
    await load();
  } catch (error: unknown) {
    correctionError.value = resolveApiError(error).message;
  } finally {
    correcting.value = false;
  }
}

function openReset(row: UserPublic) {
  currentUserId.value = row.id;
  resetForm.password = "";
  resetVisible.value = true;
}

async function saveReset() {
  if (!currentUserId.value) return;
  await resetUserPassword(currentUserId.value, resetForm.password);
  ElMessage.success("密码已重置");
  resetVisible.value = false;
}

async function toggleStatus(row: UserPublic) {
  if (row.status === "ACTIVE") {
    await ElMessageBox.confirm(`确认停用账号 ${row.username}？`, "停用账号", { type: "warning" });
    await disableUser(row.id);
  } else {
    await enableUser(row.id);
  }
  await load();
}

onMounted(load);
</script>

<template>
  <section class="list-page">
    <PageHeader
      title="系统账号"
      description="管理登录本系统使用的账号、角色和账号状态。"
    >
      <template #actions>
        <el-button type="primary" @click="openCreate">创建账号</el-button>
      </template>
    </PageHeader>

    <div class="list-panel">
      <el-table :data="users" v-loading="loading" empty-text="暂无数据">
        <el-table-column prop="username" label="用户名" width="160" />
        <el-table-column label="绑定人员">
          <template #default="{ row }">
            {{ row.employee ? `${row.employee.name} (${row.employee.employee_no})` : "-" }}
          </template>
        </el-table-column>
        <el-table-column label="角色" width="140">
          <template #default="{ row }">
            {{ ROLE_LABELS[row.role_code] ?? row.role_name }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <StatusTag kind="account" :code="row.status" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button text type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button text type="primary" @click="openReset(row)">重置密码</el-button>
            <el-button
              text
              :type="row.status === 'ACTIVE' ? 'danger' : 'primary'"
              @click="toggleStatus(row)"
            >
              {{ row.status === "ACTIVE" ? "停用" : "启用" }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" title="创建系统账号" width="520px">
      <el-form label-width="90px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="初始密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_id" style="width: 100%">
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="`${roleLabel(role)} (${role.code})`"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="绑定人员">
          <el-select v-model="form.employee_id" clearable filterable style="width: 100%">
            <el-option
              v-for="employee in employees.filter((item) => !item.has_account)"
              :key="employee.id"
              :label="`${employee.name} (${employee.employee_no})`"
              :value="employee.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editVisible" title="编辑系统账号" width="520px">
      <el-form class="ibm-form" label-width="90px">
        <StableIdentifierField
          v-model="editForm.username"
          label="用户名"
          locked
          helper="稳定业务标识，普通编辑不可修改。"
          action-label="修正用户名"
          :show-action="auth.role === 'ADMIN'"
          @correct="openCorrection"
        />
        <el-form-item label="角色">
          <el-select v-model="editForm.role_id" style="width: 100%">
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="`${roleLabel(role)} (${role.code})`"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status" style="width: 100%">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="绑定人员">
          <el-select v-model="editForm.employee_id" filterable style="width: 100%">
            <el-option
              v-for="employee in employees.filter((item) => !item.has_account || item.id === editForm.employee_id)"
              :key="employee.id"
              :label="`${employee.name} (${employee.employee_no})`"
              :value="employee.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <StableIdentifierCorrectionDialog
      v-model="correctionVisible"
      title="修正用户名"
      :impact-url="editingUser ? `/api/users/${editingUser.id}/username/impact` : ''"
      current-label="当前用户名"
      :current-value="editForm.username"
      new-label="新用户名"
      :contexts="[
        {
          label: '关联人员',
          value: editingUser?.employee
            ? `${editingUser.employee.name} (${editingUser.employee.employee_no})`
            : '未绑定',
        },
        { label: '角色', value: editingUser ? (ROLE_LABELS[editingUser.role_code] ?? editingUser.role_name) : '-' },
      ]"
      notice="用户名是稳定业务标识，仅在录入错误时修正。修正不会改变该账号的内部 ID、密码和人员绑定。"
      blank-message="请填写新用户名"
      same-message="新用户名与当前用户名一致"
      :submitting="correcting"
      :error="correctionError"
      @confirm="submitCorrection"
    />

    <el-dialog v-model="resetVisible" title="重置密码" width="420px">
      <el-form label-width="90px">
        <el-form-item label="新密码">
          <el-input v-model="resetForm.password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetVisible = false">取消</el-button>
        <el-button type="primary" @click="saveReset">确认</el-button>
      </template>
    </el-dialog>
  </section>
</template>
