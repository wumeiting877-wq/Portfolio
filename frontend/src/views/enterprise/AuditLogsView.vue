<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getAuditLog, listAuditLogs, type AuditLog } from "../../api/auditLogs";
import PageHeader from "../../components/PageHeader.vue";

const loading = ref(false);
const rows = ref<AuditLog[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const operator = ref("");
const moduleFilter = ref("");
const action = ref("");
const drawerVisible = ref(false);
const detail = ref<AuditLog | null>(null);

async function load() {
  loading.value = true;
  try {
    const result = await listAuditLogs({
      operator: operator.value || undefined,
      module: moduleFilter.value || undefined,
      action: action.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    });
    rows.value = result.items;
    total.value = result.total;
  } finally {
    loading.value = false;
  }
}

async function openDetail(row: AuditLog) {
  detail.value = await getAuditLog(row.id);
  drawerVisible.value = true;
}

function formatJson(value: Record<string, unknown> | null) {
  if (!value) return "-";
  return JSON.stringify(value, null, 2);
}

onMounted(load);
</script>

<template>
  <section>
    <PageHeader title="审计日志" description="管理员与老板可查询操作记录。敏感字段已过滤。" />
    <div class="list-toolbar">
      <el-input v-model="operator" class="list-toolbar__search" placeholder="操作人" @keyup.enter="load" />
      <el-input v-model="moduleFilter" class="list-toolbar__search" placeholder="模块" @keyup.enter="load" />
      <el-input v-model="action" class="list-toolbar__search" placeholder="动作" @keyup.enter="load" />
      <el-button @click="load">查询</el-button>
    </div>
    <div class="list-panel">
      <el-table :data="rows" v-loading="loading" empty-text="暂无日志">
        <el-table-column label="时间" width="180">
          <template #default="{ row }">{{ row.created_at.replace("T", " ").slice(0, 19) }}</template>
        </el-table-column>
        <el-table-column label="操作人" width="120">
          <template #default="{ row }">{{ row.operator_username || "-" }}</template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="120" />
        <el-table-column prop="action" label="动作" min-width="160" />
        <el-table-column label="对象" min-width="140">
          <template #default="{ row }">{{ row.target_type || "-" }} {{ row.target_id || "" }}</template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要" min-width="160" />
        <el-table-column label="操作" width="88" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="openDetail(row)">详情</el-button>
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
    <el-drawer v-model="drawerVisible" title="审计详情" size="480px">
      <template v-if="detail">
        <h3 class="drawer-title">变更前</h3>
        <pre class="json-block">{{ formatJson(detail.before_data) }}</pre>
        <h3 class="drawer-title">变更后</h3>
        <pre class="json-block">{{ formatJson(detail.after_data) }}</pre>
      </template>
    </el-drawer>
  </section>
</template>

<style scoped>
.drawer-title {
  margin: 0 0 var(--space-2);
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
}

.json-block {
  margin: 0 0 var(--space-5);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  background: var(--color-bg-page);
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
}
</style>
