<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  listNotifications,
  markNotificationRead,
  markNotificationResolved,
  refreshNotifications,
  type NotificationItem,
} from "../../api/notifications";
import PageHeader from "../../components/PageHeader.vue";
import StatusTag from "../../components/StatusTag.vue";

const router = useRouter();
const loading = ref(false);
const rows = ref<NotificationItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const statusFilter = ref("");
const typeFilter = ref("");

async function load() {
  loading.value = true;
  try {
    const result = await listNotifications({
      status: statusFilter.value || undefined,
      type: typeFilter.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    });
    rows.value = result.items;
    total.value = result.total;
  } finally {
    loading.value = false;
  }
}

async function refresh() {
  loading.value = true;
  try {
    await refreshNotifications();
    await load();
  } finally {
    loading.value = false;
  }
}

async function markRead(row: NotificationItem) {
  await markNotificationRead(row.id);
  await load();
}

async function markResolved(row: NotificationItem) {
  await markNotificationResolved(row.id);
  await load();
}

function openResource(row: NotificationItem) {
  if (row.resource_account_id) {
    void router.push({ name: "resource-detail", params: { id: row.resource_account_id } });
  }
}

onMounted(load);
</script>

<template>
  <section>
    <PageHeader title="提醒中心" description="即将到期、已到期、未分配资源与周期规则提醒。">
      <template #actions>
        <el-button @click="refresh">刷新生成</el-button>
      </template>
    </PageHeader>
    <div class="list-toolbar">
      <el-select v-model="typeFilter" clearable placeholder="类型" class="list-toolbar__status" @change="load">
        <el-option label="即将到期" value="RESOURCE_EXPIRING" />
        <el-option label="已到期" value="RESOURCE_EXPIRED" />
        <el-option label="未分配" value="RESOURCE_UNASSIGNED" />
        <el-option label="周期待执行" value="RECURRING_RULE_DUE" />
      </el-select>
      <el-select v-model="statusFilter" clearable placeholder="状态" class="list-toolbar__status" @change="load">
        <el-option label="未读" value="UNREAD" />
        <el-option label="已读" value="READ" />
        <el-option label="已处理" value="RESOLVED" />
      </el-select>
      <el-button @click="load">查询</el-button>
    </div>
    <div class="list-panel">
      <el-table :data="rows" v-loading="loading" empty-text="暂无提醒">
        <el-table-column label="类型" width="140">
          <template #default="{ row }"><StatusTag kind="notification" :code="row.type" /></template>
        </el-table-column>
        <el-table-column prop="message" label="内容" min-width="240" />
        <el-table-column label="关联资源" min-width="140">
          <template #default="{ row }">{{ row.resource_name || "-" }}</template>
        </el-table-column>
        <el-table-column label="项目" min-width="140">
          <template #default="{ row }">{{ row.project_name || "-" }}</template>
        </el-table-column>
        <el-table-column label="到期日期" width="120">
          <template #default="{ row }">{{ row.due_date || "-" }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag kind="notification" :code="row.status" /></template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'UNREAD'" text type="primary" @click="markRead(row)">标记已读</el-button>
            <el-button v-if="row.status !== 'RESOLVED'" text type="primary" @click="markResolved(row)">标记已处理</el-button>
            <el-button v-if="row.resource_account_id" text type="primary" @click="openResource(row)">查看资源</el-button>
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
  </section>
</template>
