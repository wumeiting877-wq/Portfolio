<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { listProjects, type Project } from "../../api/projects";
import { commitImport, downloadImportTemplate, IMPORT_TYPES, previewImport, type ImportPreview } from "../../api/imports";
import { downloadExport, EXPORT_TYPES } from "../../api/exports";
import { useRouteTitle } from "../../composables/roleUi";
import { useAuthStore } from "../../stores/auth";
import PageHeader from "../../components/PageHeader.vue";

const auth = useAuthStore();
const pageTitle = useRouteTitle("import-export");
const pageDescription = computed(() =>
  auth.role === "ADMIN" ? "Excel 模板、预检后导入，以及按权限范围导出。" : "按当前权限范围导出业务数据。",
);
const tab = ref<"import" | "export">(auth.canImport ? "import" : "export");
const importType = ref("employees");
const selectedFile = ref<File | null>(null);
const preview = ref<ImportPreview | null>(null);
const previewing = ref(false);
const committing = ref(false);
const exportType = ref("expenses");
const dateFrom = ref("");
const dateTo = ref("");
const projectId = ref<number | undefined>(undefined);
const currency = ref("");
const exporting = ref(false);
const projects = ref<Project[]>([]);

const exportOptions = computed(() =>
  EXPORT_TYPES.filter((item) => (item.roles as readonly string[]).includes(auth.role)),
);

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] || null;
  preview.value = null;
}

async function downloadTemplate() {
  const blob = await downloadImportTemplate(importType.value);
  saveBlob(blob, `${importType.value}_template.xlsx`);
}

async function runPreview() {
  if (!selectedFile.value) {
    ElMessage.error("请先选择 .xlsx 文件");
    return;
  }
  previewing.value = true;
  try {
    preview.value = await previewImport(importType.value, selectedFile.value);
  } finally {
    previewing.value = false;
  }
}

async function runCommit() {
  if (!selectedFile.value || !preview.value || preview.value.invalid_rows > 0) {
    ElMessage.error("请先完成无错误的预检");
    return;
  }
  committing.value = true;
  try {
    const result = await commitImport(importType.value, selectedFile.value);
    preview.value = result;
    ElMessage.success(`已导入 ${result.created_count || 0} 行`);
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: ImportPreview } } }).response?.data?.detail;
    if (detail && typeof detail === "object" && "errors" in detail) {
      preview.value = detail;
    }
  } finally {
    committing.value = false;
  }
}

async function runExport() {
  exporting.value = true;
  try {
    const blob = await downloadExport(exportType.value, {
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
      project_id: projectId.value,
      currency: currency.value || undefined,
    });
    saveBlob(blob, `${exportType.value}.xlsx`);
  } finally {
    exporting.value = false;
  }
}

onMounted(async () => {
  const result = await listProjects({ page: 1, page_size: 100 });
  projects.value = result.items;
  if (!exportOptions.value.some((item) => item.value === exportType.value)) {
    exportType.value = exportOptions.value[0]?.value || "expenses";
  }
});
</script>

<template>
  <section>
    <PageHeader :title="pageTitle" :description="pageDescription" />

    <div class="product-tabs">
      <button
        v-if="auth.canImport"
        class="product-tab"
        :class="{ 'is-selected': tab === 'import' }"
        type="button"
        @click="tab = 'import'"
      >
        导入
      </button>
      <button class="product-tab" :class="{ 'is-selected': tab === 'export' }" type="button" @click="tab = 'export'">
        导出
      </button>
    </div>

    <div v-if="tab === 'import' && auth.canImport" class="section-panel">
      <h2 class="section-panel__title">数据类型</h2>
      <div class="list-toolbar">
        <el-select v-model="importType" class="list-toolbar__status">
          <el-option v-for="item in IMPORT_TYPES" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button @click="downloadTemplate">下载模板</el-button>
      </div>
      <div class="file-row">
        <label class="file-label">
          选择 .xlsx
          <input type="file" accept=".xlsx" @change="onFileChange" />
        </label>
        <span class="file-name">{{ selectedFile ? selectedFile.name : "未选择文件" }}</span>
      </div>
      <div class="list-toolbar">
        <el-button type="primary" :loading="previewing" @click="runPreview">预检</el-button>
        <el-button
          :disabled="!preview || preview.invalid_rows > 0 || preview.valid_rows === 0"
          :loading="committing"
          @click="runCommit"
        >
          确认导入
        </el-button>
      </div>
      <div v-if="preview" class="summary-row">
        <span>总行数 {{ preview.total_rows }}</span>
        <span>有效 {{ preview.valid_rows }}</span>
        <span>错误 {{ preview.invalid_rows }}</span>
      </div>
      <div v-if="preview" class="list-panel">
        <el-table :data="preview.errors" empty-text="无错误">
          <el-table-column prop="row" label="行" width="80" />
          <el-table-column prop="field" label="字段" width="180" />
          <el-table-column prop="message" label="说明" />
        </el-table>
      </div>
    </div>

    <div v-if="tab === 'export'" class="section-panel">
      <h2 class="section-panel__title">导出条件</h2>
      <div class="list-toolbar">
        <el-select v-model="exportType" class="list-toolbar__status">
          <el-option v-for="item in exportOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-date-picker v-model="dateFrom" type="date" value-format="YYYY-MM-DD" placeholder="开始日期" />
        <el-date-picker v-model="dateTo" type="date" value-format="YYYY-MM-DD" placeholder="结束日期" />
        <el-select v-model="projectId" clearable filterable placeholder="项目" class="list-toolbar__status">
          <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-select v-model="currency" clearable placeholder="币种" class="list-toolbar__status">
          <el-option label="人民币" value="CNY" />
          <el-option label="美元" value="USD" />
        </el-select>
        <el-button type="primary" :loading="exporting" @click="runExport">生成导出</el-button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.section-panel {
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-none);
  background: var(--color-bg-panel);
}

.section-panel__title {
  margin: 0 0 var(--space-4);
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.29;
}

.file-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin: 0 0 var(--space-4);
}

.file-label {
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 0 16px;
  border: 1px solid var(--color-border-strong);
  background: var(--color-bg-panel);
  color: var(--color-text-primary);
  font-size: 14px;
  cursor: pointer;
}

.file-label input {
  display: none;
}

.file-name {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.summary-row {
  display: flex;
  gap: var(--space-5);
  margin: 0 0 var(--space-4);
  color: var(--color-text-secondary);
  font-size: 14px;
  font-variant-numeric: tabular-nums;
}
</style>
