<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { listAuditLogs, type AuditLog } from "../../api/auditLogs";
import type { UserPublic } from "../../api/auth";
import { listEmployees, type Employee } from "../../api/employees";
import { fetchDatabaseHealth, fetchHealth } from "../../api/health";
import { listNotifications } from "../../api/notifications";
import { listProjects, type Project } from "../../api/projects";
import { listUsers } from "../../api/users";
import {
  fetchBillingCosts,
  fetchEmployeeCosts,
  fetchExpenseTrend,
  fetchExpiringResources,
  fetchOverview,
  fetchProjectCosts,
  fetchResourceStatus,
  fetchResourceTypeCosts,
  type BillingCostItem,
  type EmployeeCostItem,
  type Overview,
  type ProjectCostItem,
  type ProjectPublicCostItem,
  type ResourceStatus,
  type ResourceStatusBrief,
  type ResourceTypeCostItem,
  type TrendPoint,
} from "../../api/statistics";
import { useRouteTitle } from "../../composables/roleUi";
import { useAuthStore } from "../../stores/auth";
import KpiStrip, { type KpiItem } from "../../components/KpiStrip.vue";
import MoneyText from "../../components/MoneyText.vue";
import PageHeader from "../../components/PageHeader.vue";
import StatusTag from "../../components/StatusTag.vue";
import IbmChart, { type ChartSeries } from "../../components/charts/IbmChart.vue";
import { RANGE_OPTIONS, rangeFromPreset, type RangePreset } from "../../utils/dateRange";
import { amountsList, currencyLabel, formatMoney } from "../../utils/money";
import { dashboardShellFor } from "./shells";
import AdminDashboardShell from "./shells/AdminDashboardShell.vue";
import BossDashboardShell from "./shells/BossDashboardShell.vue";
import MemberDashboardShell from "./shells/MemberDashboardShell.vue";
import ProjectManagerDashboardShell from "./shells/ProjectManagerDashboardShell.vue";

const auth = useAuthStore();
const homeTitle = useRouteTitle("home");
const dashboardShell = computed(() => dashboardShellFor(auth.role));
const router = useRouter();
const apiStatus = ref("检查中...");
const dbStatus = ref("检查中...");
const preset = ref<RangePreset>("month");
const customFrom = ref("");
const customTo = ref("");
const projectId = ref<number | undefined>(undefined);
const projects = ref<Project[]>([]);
const loading = ref(false);
const overview = ref<Overview | null>(null);
const trend = ref<TrendPoint[]>([]);
const projectCosts = ref<ProjectCostItem[]>([]);
const employeeCosts = ref<EmployeeCostItem[]>([]);
const publicCosts = ref<ProjectPublicCostItem[]>([]);
const typeCosts = ref<ResourceTypeCostItem[]>([]);
const billingCosts = ref<BillingCostItem[]>([]);
const resourceStatus = ref<ResourceStatus | null>(null);
const expiring = ref<ResourceStatusBrief[]>([]);
const adminEmployees = ref<Employee[]>([]);
const adminUsers = ref<UserPublic[]>([]);
const adminAuditLogs = ref<AuditLog[]>([]);
const adminUnreadNotificationCount = ref(0);
const adminUnresolvedNotificationCount = ref(0);
const adminLoading = ref(false);

const isAdmin = computed(() => auth.role === "ADMIN");
const isMember = computed(() => auth.role === "MEMBER");
const isPm = computed(() => auth.role === "PROJECT_MANAGER");
const isBoss = computed(() => auth.role === "BOSS");
const canRank = computed(() => ["ADMIN", "BOSS", "PROJECT_MANAGER"].includes(auth.role));
const dateRange = computed(() =>
  rangeFromPreset(preset.value, { date_from: customFrom.value, date_to: customTo.value }),
);
const query = computed(() => ({
  date_from: dateRange.value.date_from,
  date_to: dateRange.value.date_to,
  project_id: projectId.value,
}));

const kpiItems = computed<KpiItem[]>(() => {
  const amounts = amountsList(overview.value?.amounts_by_currency);
  const costLines = amounts.length ? amounts.map((item) => formatMoney(item.currency, item.amount)) : ["暂无费用"];
  if (isMember.value) {
    return [
      { label: "我的本期费用", lines: costLines },
      { label: "我参与的项目", value: String(overview.value?.my_project_count ?? 0) },
      { label: "我的资源", value: String(overview.value?.my_resource_count ?? 0) },
      { label: "即将到期", value: String(overview.value?.my_expiring_resource_count ?? 0) },
    ];
  }
  return [
    { label: "本期费用", lines: costLines },
    { label: "项目数", value: String(overview.value?.project_count ?? 0) },
    { label: "使用中资源", value: String(overview.value?.active_resource_count ?? 0) },
    {
      label: "闲置 / 未分配",
      value: `${overview.value?.idle_resource_count ?? 0} / ${overview.value?.unassigned_active_resource_count ?? 0}`,
    },
    { label: "即将到期", value: String(overview.value?.expiring_soon_count ?? 0) },
  ];
});

const adminKpiItems = computed<KpiItem[]>(() => {
  const amounts = amountsList(overview.value?.amounts_by_currency);
  return [
    { label: "人员", value: String(adminEmployees.value.length || overview.value?.employee_count || 0) },
    { label: "项目", value: String(overview.value?.project_count ?? 0) },
    { label: "资源", value: String(overview.value?.resource_count ?? 0) },
    { label: "系统账号", value: String(adminUsers.value.length) },
    {
      label: "本期费用",
      lines: amounts.length ? amounts.map((item) => formatMoney(item.currency, item.amount)) : ["暂无费用"],
    },
  ];
});

const trendCategories = computed(() => [...new Set(trend.value.map((item) => item.period))]);
const trendSeries = computed<ChartSeries[]>(() => toSeries(trend.value, "period", "amount"));
const projectCategories = computed(() => uniqueNames(projectCosts.value, "project_name"));
const projectSeries = computed<ChartSeries[]>(() => toNamedSeries(projectCosts.value, "project_name", "allocated_amount", projectCategories.value));
const typeCategories = computed(() => uniqueNames(typeCosts.value, "resource_type_name"));
const typeSeries = computed<ChartSeries[]>(() => toNamedSeries(typeCosts.value, "resource_type_name", "allocated_amount", typeCategories.value));
const bossProjectCosts = computed(() => projectCosts.value.slice(0, 5));
const bossProjectCostsHasMore = computed(() => projectCosts.value.length > 5);
const employeeCategories = computed(() => uniqueNames(employeeCosts.value, "employee_name"));
const employeeSeries = computed<ChartSeries[]>(() => toNamedSeries(employeeCosts.value, "employee_name", "allocated_amount", employeeCategories.value));

function uniqueNames(items: Array<Record<string, string | number | null>>, key: string): string[] {
  return [...new Set(items.map((item) => String(item[key])))].slice(0, 5);
}

function toSeries(items: TrendPoint[], periodKey: "period", amountKey: "amount"): ChartSeries[] {
  const periods = [...new Set(items.map((item) => item[periodKey]))];
  const currencies = [...new Set(items.map((item) => item.currency))];
  return currencies.map((currency) => ({
    name: currencyLabel(currency),
    data: periods.map((period) => {
      const point = items.find((item) => item[periodKey] === period && item.currency === currency);
      return point ? Number(point[amountKey]) : null;
    }),
  }));
}

function toNamedSeries(
  items: Array<Record<string, string | number | null>>,
  nameKey: string,
  amountKey: string,
  names: string[],
): ChartSeries[] {
  const currencies = [...new Set(items.map((item) => String(item.currency)))];
  return currencies.map((currency) => ({
    name: currencyLabel(currency),
    data: names.map((name) => {
      const row = items.find((item) => String(item[nameKey]) === name && String(item.currency) === currency);
      return row ? Number(row[amountKey]) : null;
    }),
  }));
}

async function loadHealth() {
  try {
    const health = await fetchHealth();
    apiStatus.value = health.status === "ok" ? "正常" : health.status;
  } catch {
    apiStatus.value = "不可用";
  }
  try {
    const dbHealth = await fetchDatabaseHealth();
    dbStatus.value = dbHealth.status === "ok" ? "正常" : dbHealth.status;
  } catch {
    dbStatus.value = "不可用";
  }
}

async function load() {
  loading.value = true;
  try {
    const q = query.value;
    const tasks: Promise<unknown>[] = [
      fetchOverview(q).then((data) => {
        overview.value = data;
      }),
      fetchExpenseTrend(q).then((data) => {
        trend.value = data.series;
      }),
      fetchResourceTypeCosts({ ...q, limit: 5 }).then((data) => {
        typeCosts.value = data.items;
      }),
      fetchResourceStatus({ project_id: q.project_id }).then((data) => {
        resourceStatus.value = data;
      }),
      fetchExpiringResources({ project_id: q.project_id, days: 30 }).then((data) => {
        expiring.value = data.items;
      }),
    ];
    if (isBoss.value) {
      tasks.push(
        fetchProjectCosts({ ...q, limit: 6 }).then((data) => {
          projectCosts.value = data.items;
        }),
        fetchBillingCosts(q).then((data) => {
          billingCosts.value = data.items;
        }),
      );
    } else if (canRank.value && !isPm.value) {
      tasks.push(
        fetchProjectCosts({ ...q, limit: 5 }).then((data) => {
          projectCosts.value = data.items;
        }),
      );
    }
    if (isPm.value) {
      tasks.push(
        fetchEmployeeCosts({ ...q, limit: 5 }).then((data) => {
          employeeCosts.value = data.items;
          publicCosts.value = data.project_public_costs;
        }),
        fetchProjectCosts({ ...q, limit: 5 }).then((data) => {
          projectCosts.value = data.items;
        }),
      );
    }
    await Promise.all(tasks);
  } finally {
    loading.value = false;
  }
}

async function loadAdminSummary() {
  adminLoading.value = true;
  try {
    const [employees, users, auditLogs, unread, read] = await Promise.all([
      listEmployees(),
      listUsers(),
      listAuditLogs({ page: 1, page_size: 5 }),
      listNotifications({ status: "UNREAD", page: 1, page_size: 1 }),
      listNotifications({ status: "READ", page: 1, page_size: 1 }),
    ]);
    adminEmployees.value = employees;
    adminUsers.value = users;
    adminAuditLogs.value = auditLogs.items;
    adminUnreadNotificationCount.value = unread.total;
    adminUnresolvedNotificationCount.value = unread.total + read.total;
  } finally {
    adminLoading.value = false;
  }
}

function goProject(id: number) {
  void router.push({ name: "project-detail", params: { id: String(id) }, query: { tab: "expenses" } });
}

function goResource(id: number) {
  void router.push({ name: "resource-detail", params: { id: String(id) }, query: { tab: "expenses" } });
}

function goEmployee(id: number) {
  void router.push({ name: "expenses", query: { employee_id: String(id) } });
}

onMounted(async () => {
  await loadHealth();
  if (isAdmin.value) {
    await loadAdminSummary();
  }
  if (isPm.value || isMember.value) {
    const listed = await listProjects({ page: 1, page_size: 100 });
    projects.value = listed.items;
  }
  await load();
});

watch([preset, customFrom, customTo, projectId], () => {
  if (preset.value === "custom" && (!customFrom.value || !customTo.value)) return;
  void load();
});
</script>

<template>
  <AdminDashboardShell
    v-if="isAdmin"
    v-model:preset="preset"
    v-model:custom-from="customFrom"
    v-model:custom-to="customTo"
    :title="homeTitle"
    :loading="loading || adminLoading"
    :api-status="apiStatus"
    :db-status="dbStatus"
    :kpi-items="adminKpiItems"
    :resource-status="resourceStatus"
    :expiring="expiring"
    :employees="adminEmployees"
    :users="adminUsers"
    :unread-notification-count="adminUnreadNotificationCount"
    :unresolved-notification-count="adminUnresolvedNotificationCount"
    :recent-audit-logs="adminAuditLogs"
  />
  <BossDashboardShell
    v-else-if="isBoss"
    v-model:preset="preset"
    v-model:custom-from="customFrom"
    v-model:custom-to="customTo"
    :title="homeTitle"
    :loading="loading"
    :kpi-items="kpiItems"
    :trend-categories="trendCategories"
    :trend-series="trendSeries"
    :project-costs="bossProjectCosts"
    :project-costs-has-more="bossProjectCostsHasMore"
    :type-costs="typeCosts"
    :billing-costs="billingCosts"
    :resource-status="resourceStatus"
    :expiring="expiring"
  />
  <ProjectManagerDashboardShell
    v-else-if="isPm"
    v-model:preset="preset"
    v-model:custom-from="customFrom"
    v-model:custom-to="customTo"
    v-model:project-id="projectId"
    :title="homeTitle"
    :kpi-items="kpiItems"
    :projects="projects"
    :trend-categories="trendCategories"
    :trend-series="trendSeries"
    :project-costs="projectCosts"
    :type-costs="typeCosts"
    :employee-costs="employeeCosts"
    :public-costs="publicCosts"
    :resource-status="resourceStatus"
  />
  <MemberDashboardShell
    v-else-if="isMember"
    v-model:preset="preset"
    v-model:custom-from="customFrom"
    v-model:custom-to="customTo"
    :title="homeTitle"
    :kpi-items="kpiItems"
    :projects="projects"
    :trend-categories="trendCategories"
    :trend-series="trendSeries"
    :type-costs="typeCosts"
    :resource-status="resourceStatus"
    :expiring="expiring"
  />
  <component :is="dashboardShell" v-else>
  <section class="home-page">
    <PageHeader :title="homeTitle" description="统计数字来自当前权限范围内的有效费用分摊与资源分配。">
      <template #actions>
        <span class="health-meta">
          后端 <StatusTag kind="health" :code="apiStatus" />
          数据库 <StatusTag kind="health" :code="dbStatus" />
        </span>
      </template>
    </PageHeader>

    <div class="toolbar">
      <el-radio-group v-model="preset" size="small">
        <el-radio-button v-for="item in RANGE_OPTIONS" :key="item.value" :label="item.value">
          {{ item.label }}
        </el-radio-button>
      </el-radio-group>
      <template v-if="preset === 'custom'">
        <el-date-picker v-model="customFrom" value-format="YYYY-MM-DD" placeholder="开始日期" />
        <el-date-picker v-model="customTo" value-format="YYYY-MM-DD" placeholder="结束日期" />
      </template>
      <el-select
        v-if="isPm && projects.length > 1"
        v-model="projectId"
        clearable
        placeholder="我的负责项目"
        style="width: 220px"
      >
        <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
    </div>

    <KpiStrip :items="kpiItems" />

    <div class="dash-grid dash-grid--main">
      <section class="panel">
        <h2 class="panel__title">费用趋势</h2>
        <IbmChart kind="line" :categories="trendCategories" :series="trendSeries" height="300px" empty-title="当前时间范围暂无费用数据" />
      </section>
      <section class="panel">
        <h2 class="panel__title">资源状态</h2>
        <el-table
          v-if="resourceStatus"
          :data="[
            { name: '使用中', value: resourceStatus.counts.ACTIVE || 0 },
            { name: '闲置', value: resourceStatus.explicit_idle_count },
            { name: '未分配但仍使用中', value: resourceStatus.unassigned_active_count },
            { name: '即将到期', value: resourceStatus.counts.EXPIRING_SOON || 0 },
            { name: '已到期', value: resourceStatus.counts.EXPIRED || 0 },
            { name: '已停用', value: resourceStatus.counts.DISABLED || 0 },
          ]"
          empty-text="当前没有资源数据"
        >
          <el-table-column prop="name" label="状态" />
          <el-table-column prop="value" label="数量" width="88" align="right" />
        </el-table>
      </section>
    </div>

    <div v-if="!isMember" class="dash-grid">
      <section v-if="canRank" class="panel">
        <h2 class="panel__title">{{ isPm ? "我的项目费用" : "项目费用 Top 5" }}</h2>
        <IbmChart kind="bar" :categories="projectCategories" :series="projectSeries" height="280px" empty-title="当前时间范围暂无项目费用" />
        <el-table :data="projectCosts" empty-text="当前时间范围暂无项目费用">
          <el-table-column label="项目" min-width="160">
            <template #default="{ row }">
              <button class="linkish" type="button" @click="goProject(row.project_id)">{{ row.project_name }}</button>
            </template>
          </el-table-column>
          <el-table-column label="金额" align="right" width="180">
            <template #default="{ row }">
              <MoneyText :currency="row.currency" :amount="row.allocated_amount" />
            </template>
          </el-table-column>
        </el-table>
      </section>
      <section class="panel">
        <h2 class="panel__title">{{ isMember ? "我的资源类型费用" : "资源类型费用 Top 5" }}</h2>
        <IbmChart kind="bar" :categories="typeCategories" :series="typeSeries" height="280px" empty-title="当前时间范围暂无资源类型费用" />
      </section>
    </div>

    <section v-if="isMember" class="panel">
      <h2 class="panel__title">我的资源类型费用</h2>
      <IbmChart kind="bar" :categories="typeCategories" :series="typeSeries" height="280px" empty-title="当前时间范围暂无费用数据" />
    </section>

    <section v-if="isPm" class="panel">
      <h2 class="panel__title">项目成员费用</h2>
      <IbmChart kind="bar" :categories="employeeCategories" :series="employeeSeries" height="260px" empty-title="当前没有成员直接费用" />
      <el-table :data="employeeCosts" empty-text="当前没有成员直接费用">
        <el-table-column label="成员" min-width="140">
          <template #default="{ row }">
            <button class="linkish" type="button" @click="goEmployee(row.employee_id)">{{ row.employee_name }}</button>
          </template>
        </el-table-column>
        <el-table-column label="金额" align="right" width="180">
          <template #default="{ row }">
            <MoneyText :currency="row.currency" :amount="row.allocated_amount" />
          </template>
        </el-table-column>
      </el-table>
      <p v-if="publicCosts.length" class="hint">项目公共费用单独列出，不摊入成员。</p>
      <el-table v-if="publicCosts.length" :data="publicCosts">
        <el-table-column prop="project_name" label="项目" />
        <el-table-column label="公共费用" align="right">
          <template #default="{ row }">
            <MoneyText :currency="row.currency" :amount="row.allocated_amount" />
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="panel">
      <h2 class="panel__title">即将到期资源</h2>
      <el-table :data="expiring" empty-text="当前没有即将到期资源">
        <el-table-column label="资源" min-width="180">
          <template #default="{ row }">
            <button class="linkish" type="button" @click="goResource(row.id)">{{ row.resource_name }}</button>
          </template>
        </el-table-column>
        <el-table-column prop="resource_type_name" label="类型" width="140" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <StatusTag kind="resource" :code="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="expires_at" label="到期日" width="120" />
        <el-table-column prop="days_remaining" label="剩余天数" width="100" align="right" />
      </el-table>
    </section>

    <div v-if="!isMember && resourceStatus" class="dash-grid">
      <section class="panel">
        <h2 class="panel__title">闲置资源</h2>
        <el-table :data="resourceStatus.idle_resources" empty-text="当前没有闲置资源">
          <el-table-column label="资源" min-width="180">
            <template #default="{ row }">
              <button class="linkish" type="button" @click="goResource(row.id)">{{ row.resource_name }}</button>
            </template>
          </el-table-column>
          <el-table-column prop="resource_type_name" label="类型" />
        </el-table>
      </section>
      <section class="panel">
        <h2 class="panel__title">未分配但仍使用中</h2>
        <el-table :data="resourceStatus.unassigned_active_resources" empty-text="当前没有未分配的使用中资源">
          <el-table-column label="资源" min-width="180">
            <template #default="{ row }">
              <button class="linkish" type="button" @click="goResource(row.id)">{{ row.resource_name }}</button>
            </template>
          </el-table-column>
          <el-table-column prop="resource_type_name" label="类型" />
        </el-table>
      </section>
    </div>
  </section>
  </component>
</template>

<style scoped>
.home-page {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.health-meta {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-secondary);
  font-size: 12px;
  letter-spacing: 0.32px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}

.panel {
  min-width: 0;
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  background: var(--color-bg-panel);
}

.panel__title {
  margin: 0 0 var(--space-3);
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 400;
  line-height: 1.5;
  letter-spacing: 0.16px;
}

.dash-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-5);
}

.dash-grid--main {
  grid-template-columns: 2fr 1fr;
}

.linkish {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--color-link);
  cursor: pointer;
  font: inherit;
}

.hint {
  margin: var(--space-3) 0 var(--space-2);
  color: var(--color-text-secondary);
  font-size: 12px;
}

@media (max-width: 1024px) {
  .dash-grid,
  .dash-grid--main {
    grid-template-columns: 1fr;
  }
}
</style>
