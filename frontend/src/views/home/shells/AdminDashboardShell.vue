<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import type { AuditLog } from "../../../api/auditLogs";
import type { UserPublic } from "../../../api/auth";
import type { Employee } from "../../../api/employees";
import type { ResourceStatus, ResourceStatusBrief } from "../../../api/statistics";
import KpiStrip, { type KpiItem } from "../../../components/KpiStrip.vue";
import PageHeader from "../../../components/PageHeader.vue";
import StatusTag from "../../../components/StatusTag.vue";
import type { RangePreset } from "../../../utils/dateRange";
import DashboardDateFilter from "../components/DashboardDateFilter.vue";
import ResourceStatusBars from "../components/ResourceStatusBars.vue";

const preset = defineModel<RangePreset>("preset", { required: true });
const customFrom = defineModel<string>("customFrom", { required: true });
const customTo = defineModel<string>("customTo", { required: true });
const props = defineProps<{
  title: string;
  loading: boolean;
  apiStatus: string;
  dbStatus: string;
  kpiItems: KpiItem[];
  resourceStatus: ResourceStatus | null;
  expiring: ResourceStatusBrief[];
  employees: Employee[];
  users: UserPublic[];
  unreadNotificationCount: number;
  unresolvedNotificationCount: number;
  recentAuditLogs: AuditLog[];
}>();

const router = useRouter();
const employeeCounts = computed(() => countBy(props.employees, "employment_status"));
const userCounts = computed(() => countBy(props.users, "status"));
const expiringCount = computed(() => props.resourceStatus?.counts.EXPIRING_SOON || 0);
const idleCount = computed(() => props.resourceStatus?.explicit_idle_count || 0);
const unassignedCount = computed(() => props.resourceStatus?.unassigned_active_count || 0);

function countBy<T, K extends keyof T>(items: T[], key: K) {
  return items.reduce<Record<string, number>>((result, item) => {
    const value = String(item[key] ?? "UNKNOWN");
    result[value] = (result[value] || 0) + 1;
    return result;
  }, {});
}

function go(name: string) {
  void router.push({ name });
}

function goResource(id: number) {
  void router.push({ name: "resource-detail", params: { id: String(id) } });
}

function formatAuditTime(value: string) {
  return value.replace("T", " ").slice(0, 16);
}

function auditTarget(row: AuditLog) {
  return row.summary || [row.target_type, row.target_id].filter(Boolean).join(" ") || "-";
}
</script>

<template>
  <section class="dashboard" data-dashboard="admin">
    <PageHeader :title="title" description="系统状态、基础数据、资源事项与最近管理操作。" />
    <section class="panel system-panel">
      <h2 class="panel__title">系统状态</h2>
      <div class="system-status">
        <div class="system-status__item"><span>后端服务</span><StatusTag kind="health" :code="apiStatus" /></div>
        <div class="system-status__item"><span>数据库连接</span><StatusTag kind="health" :code="dbStatus" /></div>
      </div>
    </section>

    <section class="summary-section">
      <div class="section-head">
        <h2 class="section-title">基础数据概况</h2>
        <DashboardDateFilter v-model:preset="preset" v-model:custom-from="customFrom" v-model:custom-to="customTo" />
      </div>
      <KpiStrip :items="kpiItems" :columns="5" />
    </section>

    <div class="grid grid--primary">
      <section class="panel"><h2 class="panel__title">资源状态</h2><ResourceStatusBars :status="resourceStatus" /></section>
      <section class="panel">
        <div class="panel__head"><h2 class="panel__title">待处理事项</h2><button class="linkish" type="button" @click="go('notifications')">查看提醒中心</button></div>
        <div class="pending-list">
          <button class="pending-item" type="button" @click="go('resources')"><span>即将到期资源</span><strong>{{ expiringCount }}</strong></button>
          <button class="pending-item" type="button" @click="go('resources')"><span>未分配活跃资源</span><strong>{{ unassignedCount }}</strong></button>
          <button class="pending-item" type="button" @click="go('resources')"><span>闲置资源</span><strong>{{ idleCount }}</strong></button>
          <button class="pending-item" type="button" @click="go('notifications')"><span>未解决提醒 <small>其中未读 {{ unreadNotificationCount }}</small></span><strong>{{ unresolvedNotificationCount }}</strong></button>
        </div>
        <div v-if="expiring.length" class="expiring-links"><span>近期：</span><button v-for="item in expiring.slice(0, 3)" :key="item.id" class="linkish" type="button" @click="goResource(item.id)">{{ item.resource_name }}</button></div>
      </section>
    </div>

    <div class="grid">
      <section class="panel">
        <div class="panel__head"><h2 class="panel__title">账号与人员概况</h2><div class="panel-links"><button class="linkish" type="button" @click="go('employees')">人员管理</button><button class="linkish" type="button" @click="go('users')">系统账号</button></div></div>
        <div class="account-block">
          <div class="account-block__head"><span>人员</span><strong>{{ employees.length }}</strong></div>
          <dl><div><dt>在职</dt><dd>{{ employeeCounts.ACTIVE || 0 }}</dd></div><div><dt>停用</dt><dd>{{ employeeCounts.INACTIVE || 0 }}</dd></div><div><dt>离职</dt><dd>{{ employeeCounts.LEFT || 0 }}</dd></div></dl>
        </div>
        <div class="account-block">
          <div class="account-block__head"><span>系统账号</span><strong>{{ users.length }}</strong></div>
          <dl><div><dt>正常</dt><dd>{{ userCounts.ACTIVE || 0 }}</dd></div><div><dt>已停用</dt><dd>{{ userCounts.DISABLED || 0 }}</dd></div><div><dt>已锁定</dt><dd>{{ userCounts.LOCKED || 0 }}</dd></div></dl>
        </div>
      </section>
      <section class="panel">
        <div class="panel__head"><h2 class="panel__title">最近操作</h2><button class="linkish" type="button" @click="go('audit-logs')">查看全部</button></div>
        <el-table :data="recentAuditLogs" size="small" empty-text="暂无操作记录" v-loading="loading">
          <el-table-column label="时间" width="132"><template #default="{ row }">{{ formatAuditTime(row.created_at) }}</template></el-table-column>
          <el-table-column label="操作人" width="104"><template #default="{ row }">{{ row.operator_username || "-" }}</template></el-table-column>
          <el-table-column prop="action" label="动作" min-width="138" />
          <el-table-column label="对象" min-width="148" show-overflow-tooltip><template #default="{ row }">{{ auditTarget(row) }}</template></el-table-column>
        </el-table>
      </section>
    </div>

    <section class="panel quick-panel">
      <h2 class="panel__title">常用管理</h2>
      <nav class="quick-links" aria-label="常用管理入口">
        <button class="linkish" type="button" @click="go('employees')">人员管理</button><button class="linkish" type="button" @click="go('users')">系统账号</button><button class="linkish" type="button" @click="go('projects')">项目管理</button><button class="linkish" type="button" @click="go('resources')">资源账号</button><button class="linkish" type="button" @click="go('expenses')">费用管理</button><button class="linkish" type="button" @click="go('import-export')">导入导出</button><button class="linkish" type="button" @click="go('settings')">系统设置</button>
      </nav>
    </section>
  </section>
</template>

<style scoped>
.dashboard{min-width:0;display:flex;flex-direction:column;gap:var(--space-4)}.dashboard :deep(.page-header){margin-bottom:0}.panel{min-width:0;padding:var(--space-4);border:1px solid var(--color-border);background:var(--color-bg-panel)}.panel__head,.section-head{display:flex;align-items:center;justify-content:space-between;gap:var(--space-4)}.panel__title,.section-title{margin:0 0 var(--space-3);color:var(--color-text-primary);font-size:16px;font-weight:400;line-height:1.5;letter-spacing:.16px}.section-head .section-title{margin:0}.system-panel{display:grid;grid-template-columns:minmax(160px,1fr) minmax(0,3fr);align-items:center}.system-panel .panel__title{margin:0}.system-status{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));border-left:1px solid var(--color-border)}.system-status__item{display:flex;align-items:center;justify-content:space-between;gap:var(--space-4);min-height:40px;padding:0 var(--space-4);border-right:1px solid var(--color-border);color:var(--color-text-secondary);font-size:14px}.summary-section{display:flex;flex-direction:column;gap:var(--space-3)}.grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:var(--space-4);align-items:stretch}.grid--primary{grid-template-columns:minmax(0,1.15fr) minmax(340px,.85fr)}.linkish{padding:0;border:0;background:transparent;color:var(--color-link);cursor:pointer;font:inherit;text-align:left}.linkish:hover{text-decoration:underline;text-underline-offset:2px}.linkish:focus-visible,.pending-item:focus-visible{outline:2px solid var(--color-focus);outline-offset:2px}.panel-links,.quick-links{display:flex;flex-wrap:wrap;gap:var(--space-4)}.pending-list{border-top:1px solid var(--color-border)}.pending-item{display:flex;width:100%;align-items:center;justify-content:space-between;gap:var(--space-3);min-height:40px;padding:6px 0;border:0;border-bottom:1px solid var(--color-border);background:transparent;color:var(--color-text-primary);cursor:pointer;font:inherit;text-align:left}.pending-item:hover span{color:var(--color-link)}.pending-item strong,.account-block__head strong{font-size:20px;font-weight:400;font-variant-numeric:tabular-nums}.pending-item small{display:block;color:var(--color-text-muted);font-size:11px}.expiring-links{display:flex;flex-wrap:wrap;gap:var(--space-2);margin-top:var(--space-3);color:var(--color-text-secondary);font-size:12px}.account-block{padding:var(--space-3) 0;border-top:1px solid var(--color-border)}.account-block:first-of-type{border-top:0}.account-block__head{display:flex;align-items:baseline;justify-content:space-between}.account-block dl{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));margin:var(--space-2) 0 0}.account-block dl div{display:flex;justify-content:space-between;gap:var(--space-2);padding-right:var(--space-3);color:var(--color-text-secondary);font-size:12px}.account-block dt,.account-block dd{margin:0}.account-block dd{color:var(--color-text-primary);font-variant-numeric:tabular-nums}.quick-panel .panel__title{margin-bottom:var(--space-2)}.quick-links .linkish{min-height:32px}.dashboard :deep(.el-table .el-table__cell){padding:6px 0}.dashboard :deep(.el-table__empty-block){min-height:48px}@media(max-width:980px){.grid,.grid--primary,.system-panel{grid-template-columns:1fr}.system-status{border-top:1px solid var(--color-border);border-left:0}.section-head{align-items:flex-start;flex-direction:column}}@media(max-width:672px){.system-status{grid-template-columns:1fr}.system-status__item{border-right:0;border-bottom:1px solid var(--color-border)}.account-block dl{grid-template-columns:1fr;gap:var(--space-2)}}
</style>
