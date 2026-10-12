<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  correctEmployeeNo,
  createEmployee,
  disableEmployee,
  listEmployees,
  updateEmployee,
  type Employee,
} from "../../api/employees";
import { useAuthStore } from "../../stores/auth";
import PageHeader from "../../components/PageHeader.vue";
import StableIdentifierCorrectionDialog from "../../components/StableIdentifierCorrectionDialog.vue";
import StableIdentifierField from "../../components/StableIdentifierField.vue";
import StatusTag from "../../components/StatusTag.vue";
import { applyApiFieldErrors, resolveApiError } from "../../utils/apiError";
import { hasText, isEmail } from "../../utils/formRules";

const auth = useAuthStore();
const loading = ref(false);
const keyword = ref("");
const rows = ref<Employee[]>([]);
const dialogVisible = ref(false);
const correctionVisible = ref(false);
const correcting = ref(false);
const correctionError = ref("");
const editingId = ref<number | null>(null);
const editingName = ref("");
const form = reactive({
  employee_no: "",
  name: "",
  department: "",
  position: "",
  email: "",
  phone: "",
  remark: "",
});
const errors = reactive({
  employee_no: "",
  name: "",
  email: "",
});

async function load() {
  loading.value = true;
  try {
    rows.value = await listEmployees({ q: keyword.value || undefined });
  } finally {
    loading.value = false;
  }
}

function clearErrors() {
  errors.employee_no = "";
  errors.name = "";
  errors.email = "";
}

function openCreate() {
  editingId.value = null;
  clearErrors();
  Object.assign(form, {
    employee_no: "",
    name: "",
    department: "",
    position: "",
    email: "",
    phone: "",
    remark: "",
  });
  dialogVisible.value = true;
}

function openEdit(row: Employee) {
  editingId.value = row.id;
  editingName.value = row.name;
  clearErrors();
  Object.assign(form, {
    employee_no: row.employee_no,
    name: row.name,
    department: row.department || "",
    position: row.position || "",
    email: row.email || "",
    phone: row.phone || "",
    remark: row.remark || "",
  });
  dialogVisible.value = true;
}

function validateForm() {
  clearErrors();
  if (!editingId.value && !hasText(form.employee_no)) errors.employee_no = "请输入工号";
  if (!hasText(form.name)) errors.name = "请输入姓名";
  if (hasText(form.email) && !isEmail(form.email)) errors.email = "请输入正确的邮箱地址";
  return !errors.employee_no && !errors.name && !errors.email;
}

async function save() {
  if (!validateForm()) return;
  const payload = {
    employee_no: form.employee_no.trim(),
    name: form.name.trim(),
    department: form.department,
    position: form.position,
    email: form.email.trim(),
    phone: form.phone,
    remark: form.remark,
  };
  try {
    if (editingId.value) {
      const { employee_no: _employeeNo, ...updatePayload } = payload;
      await updateEmployee(editingId.value, updatePayload);
      ElMessage.success("已保存");
    } else {
      await createEmployee(payload);
      ElMessage.success("已创建");
    }
  } catch (error: unknown) {
    applyApiFieldErrors(error, errors);
    return;
  }
  dialogVisible.value = false;
  await load();
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
    const updated = await correctEmployeeNo(editingId.value, nextValue);
    form.employee_no = updated.employee_no;
    editingName.value = updated.name;
    correctionVisible.value = false;
    ElMessage.success("工号已修正");
    await load();
  } catch (error: unknown) {
    correctionError.value = resolveApiError(error).message;
  } finally {
    correcting.value = false;
  }
}

async function disable(row: Employee) {
  await ElMessageBox.confirm(`确认停用人员 ${row.name}？`, "停用人员", { type: "warning" });
  await disableEmployee(row.id);
  ElMessage.success("已停用");
  await load();
}

onMounted(load);
</script>

<template>
  <section class="list-page">
    <PageHeader title="人员管理">
      <template v-if="auth.canWriteEmployees" #actions>
        <el-button type="primary" @click="openCreate">新建人员</el-button>
      </template>
    </PageHeader>

    <div class="list-toolbar">
      <el-input
        v-model="keyword"
        class="list-toolbar__search"
        placeholder="搜索姓名或工号"
        @keyup.enter="load"
      />
      <el-button @click="load">查询</el-button>
    </div>

    <div class="list-panel">
      <el-table :data="rows" v-loading="loading" empty-text="暂无数据">
        <el-table-column prop="employee_no" label="工号" width="140" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="department" label="部门" />
        <el-table-column prop="position" label="岗位" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <StatusTag kind="employee" :code="row.employment_status" />
          </template>
        </el-table-column>
        <el-table-column v-if="auth.canWriteEmployees" label="操作" width="160">
          <template #default="{ row }">
            <el-button text type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button
              text
              type="danger"
              :disabled="row.employment_status !== 'ACTIVE'"
              @click="disable(row)"
            >
              停用
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑人员' : '新建人员'" width="520px">
      <el-form class="ibm-form" label-width="80px">
        <StableIdentifierField
          v-model="form.employee_no"
          label="工号"
          required
          :locked="Boolean(editingId)"
          :maxlength="50"
          :error="errors.employee_no"
          helper="稳定业务标识，普通编辑不可修改。"
          action-label="修正工号"
          :show-action="auth.role === 'ADMIN'"
          @correct="openCorrection"
        />
        <el-form-item :error="errors.name">
          <template #label>姓名<span class="field-required">*</span></template>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="form.department" />
        </el-form-item>
        <el-form-item label="岗位">
          <el-input v-model="form.position" />
        </el-form-item>
        <el-form-item :error="errors.email" label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <StableIdentifierCorrectionDialog
      v-model="correctionVisible"
      title="修正工号"
      :impact-url="editingId ? `/api/employees/${editingId}/employee-no/impact` : ''"
      subject-label="人员"
      :subject-value="editingName"
      current-label="当前工号"
      :current-value="form.employee_no"
      new-label="新工号"
      notice="工号是稳定业务标识，仅在录入错误时修正。修正不会改变该人员的内部 ID 和已有业务关联。"
      blank-message="请填写新工号"
      same-message="新工号与当前工号一致"
      :submitting="correcting"
      :error="correctionError"
      @confirm="submitCorrection"
    />
  </section>
</template>
