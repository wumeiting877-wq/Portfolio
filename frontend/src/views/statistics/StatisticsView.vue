<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { listProjects, type Project } from "../../api/projects";
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
import IbmChart, { type ChartSeries } from "../../components/charts/IbmChart.vue";
import { RANGE_OPTIONS, rangeFromPreset, type RangePreset } from "../../utils/dateRange";
import { amountsList, currencyLabel, formatMoney } from "../../utils/money";

const auth = useAuthStore();
const pageTitle = useRouteTitle("statistics");
const router = useRouter();
const preset = ref<RangePreset>("month");
const customFrom = ref("");
const customTo = ref("");
const projectId = ref<number | undefined>(undefined);
const limit = ref(10);
const tab = ref("trend");
const projects = ref<Project[]>([]);
const overview = ref<Overview | null>(null);
const trend = ref<TrendPoint[]>([]);
const projectCosts = ref<ProjectCostItem[]>([]);
const employeeCosts = ref<EmployeeCostItem[]>([]);
const publicCosts = ref<ProjectPublicCostItem[]>([]);
const typeCosts = ref<ResourceTypeCostItem[]>([]);
const billingCosts = ref<BillingCostItem[]>([]);
const resourceStatus = ref<ResourceStatus | null>(null);
const expiring = ref<ResourceStatusBrief[]>([]);

const isMember = computed(() => auth.role === "MEMBER");
const canRank = computed(() => ["ADMIN", "BOSS", "PROJECT_MANAGER"].includes(auth.role));
const dateRange = computed(() =>
  rangeFromPreset(preset.value, { date_from: customFrom.value, date_to: customTo.value }),
);
const query = computed(() => ({
  date_from: dateRange.value.date_from,
  date_to: dateRange.value.date_to,
  project_id: projectId.value,
  limit: limit.value,
}));

const tabs = computed(() => {
  if (isMember.value) {
    return [
      { id: "trend", label: "我的费用" },
      { id: "types", label: "我的资源" },
    ];
  }
  const items = [
    { id: "trend", label: "费用趋势" },
    { id: "projects", label: auth.role === "PROJECT_MANAGER" ? "我的项目" : "项目" },
    { id: "employees", label: "成员" },
    { id: "types", label: "资源类型" },
    { id: "billing", label: "费用类型" },
    { id: "resources", label: "资源状态" },
  ];
  return items;
});

const kpiItems = computed<KpiItem[]>(() => {
  const amounts = amountsList(overview.value?.amounts_by_currency);
  const costLines = amounts.length ? amounts.map((item) => formatMoney(item.currency, item.amount)) : ["暂无费用"];
  if (isMember.value) {
    return [
      { label: "我的本期费用", lines: costLines },
      { label: "我的资源", value: String(overview.value?.my_resource_count ?? 0) },
      { label: "即将到期", value: String(overview.value?.my_expiring_resource_count ?? 0) },
    ];
  }
  return [
    { label: "本期费用", lines: costLines },
    { label: "项目数", value: String(overview.value?.project_count ?? 0) },
    { label: "资源数", value: String(overview.value?.resource_count ?? 0) },
    { label: "闲置 / 未分配", value: `${overview.value?.idle_resource_count ?? 0} / ${overview.value?.unassigned_active_resource_count ?? 0}` },
  ];
});

const trendCategories = computed(() => [...new Set(trend.value.map((item) => item.period))]);
const trendSeries = computed<ChartSeries[]>(() => {
  const periods = trendCategories.value;
  const currencies = [...new Set(trend.value.map((item) => item.currency))];
  return currencies.map((currency) => ({
    name: currencyLabel(currency),
    data: periods.map((period) => {
      const point = trend.value.find((item) => item.period === period && item.currency === currency);
      return point ? Number(point.amount) : null;
    }),
  }));
});

async function load() {
  const q = query.value;
  overview.value = await fetchOverview(q);
  trend.value = (await fetchExpenseTrend(q)).series;
  typeCosts.value = (await fetchResourceTypeCosts(q)).items;
  resourceStatus.value = await fetchResourceStatus({ project_id: q.project_id });
  expiring.value = (await fetchExpiringResources({ project_id: q.project_id, days: 30 })).items;
  billingCosts.value = (await fetchBillingCosts(q)).items;
  if (canRank.value) {
    projectCosts.value = (await fetchProjectCosts(q)).items;
    const employees = await fetchEmployeeCosts(q);
    employeeCosts.value = employees.items;
    publicCosts.value = employees.project_public_costs;
  }
}

function goProject(id: number) {
  void router.push({ name: "project-detail", params: { id: String(id) }, query: { tab: "expenses" } });
}

function goEmployee(id: number) {
  void router.push({ name: "expenses", query: { employee_id: String(id) } });
}

function goResource(id: number) {
  void router.push({ name: "resource-detail", params: { id: String(id) }, query: { tab: "expenses" } });
}

onMounted(async () => {
  if (auth.role === "PROJECT_MANAGER") {
    projects.value = (await listProjects({ page: 1, page_size: 100 })).items;
  }
  tab.value = tabs.value[0].id;
  await load();
});

watch([preset, customFrom, customTo, projectId, limit], () => {
  if (preset.value === "custom" && (!customFrom.value || !customTo.value)) return;
  void load();
});
</script>

<template>
  <section class="stats-page">
    <PageHeader :title="pageTitle" description="按币种分别汇总当前权限范围内的有效分摊，不进行跨币种相加。" />
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
        v-if="auth.role === 'PROJECT_MANAGER' && projects.length > 1"
        v-model="projectId"
        clearable
        placeholder="我的负责项目"
        style="width: 220px"
      >
        <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select v-if="canRank" v-model="limit" style="width: 120px">
        <el-option :value="10" label="Top 10" />
        <el-option :value="20" label="Top 20" />
      </el-select>
    </div>
    <KpiStrip :items="kpiItems" />
    <div class="product-tabs">
      <button
        v-for="item in tabs"
        :key="item.id"
        class="product-tab"
        :class="{ 'is-selected': tab === item.id }"
        type="button"
        @click="tab = item.id"
      >
        {{ item.label }}
      </button>
    </div>

    <section v-if="tab === 'trend'" class="panel">
      <h2 class="panel__title">费用趋势</h2>
      <IbmChart kind="line" :categories="trendCategories" :series="trendSeries" height="320px" empty-title="当前时间范围暂无费用数据" />
    </section>

    <section v-if="tab === 'projects' && canRank" class="panel">
      <h2 class="panel__title">项目费用</h2>
      <el-table :data="projectCosts" empty-text="当前时间范围暂无项目费用">
        <el-table-column label="项目" min-width="180">
          <template #default="{ row }">
            <button class="linkish" type="button" @click="goProject(row.project_id)">{{ row.project_name }}</button>
          </template>
        </el-table-column>
        <el-table-column label="币种" width="88"><template #default="{ row }">{{ currencyLabel(row.currency) }}</template></el-table-column>
        <el-table-column label="分摊金额" align="right" width="180">
          <template #default="{ row }">
            <MoneyText :currency="row.currency" :amount="row.allocated_amount" />
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section v-if="tab === 'employees' && canRank" class="panel">
      <h2 class="panel__title">成员费用</h2>
      <el-table :data="employeeCosts" empty-text="当前没有成员直接费用">
        <el-table-column label="成员" min-width="160">
          <template #default="{ row }">
            <button class="linkish" type="button" @click="goEmployee(row.employee_id)">{{ row.employee_name }}</button>
          </template>
        </el-table-column>
        <el-table-column prop="employee_no" label="工号" width="140" />
        <el-table-column label="币种" width="88"><template #default="{ row }">{{ currencyLabel(row.currency) }}</template></el-table-column>
        <el-table-column label="分摊金额" align="right" width="180">
          <template #default="{ row }">
            <MoneyText :currency="row.currency" :amount="row.allocated_amount" />
          </template>
        </el-table-column>
      </el-table>
      <h2 class="panel__title" style="margin-top: 24px">项目公共费用</h2>
      <el-table :data="publicCosts" empty-text="当前没有项目公共费用">
        <el-table-column prop="project_name" label="项目" min-width="180" />
        <el-table-column label="币种" width="88"><template #default="{ row }">{{ currencyLabel(row.currency) }}</template></el-table-column>
        <el-table-column label="分摊金额" align="right" width="180">
          <template #default="{ row }">
            <MoneyText :currency="row.currency" :amount="row.allocated_amount" />
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section v-if="tab === 'types'" class="panel">
      <h2 class="panel__title">资源类型费用</h2>
      <el-table :data="typeCosts" empty-text="当前时间范围暂无费用数据">
        <el-table-column prop="resource_type_name" label="资源类型" min-width="180" />
        <el-table-column prop="resource_type_code" label="编码" width="140" />
        <el-table-column label="币种" width="88"><template #default="{ row }">{{ currencyLabel(row.currency) }}</template></el-table-column>
        <el-table-column label="分摊金额" align="right" width="180">
          <template #default="{ row }">
            <MoneyText :currency="row.currency" :amount="row.allocated_amount" />
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section v-if="tab === 'billing'" class="panel">
      <h2 class="panel__title">计费方式 / 费用类别</h2>
      <el-table :data="billingCosts" empty-text="当前时间范围暂无费用数据">
        <el-table-column prop="billing_mode" label="计费方式" width="140" />
        <el-table-column prop="category" label="类别" width="160" />
        <el-table-column label="币种" width="88"><template #default="{ row }">{{ currencyLabel(row.currency) }}</template></el-table-column>
        <el-table-column label="分摊金额" align="right" width="180">
          <template #default="{ row }">
            <MoneyText :currency="row.currency" :amount="row.allocated_amount" />
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section v-if="tab === 'resources' || (isMember && tab === 'types')" class="panel">
      <h2 v-if="!isMember || tab === 'types'" class="panel__title">{{ isMember ? "我的即将到期资源" : "资源状态" }}</h2>
      <el-table
        v-if="resourceStatus && !isMember"
        :data="[
          { name: '使用中', value: resourceStatus.counts.ACTIVE || 0 },
          { name: '闲置', value: resourceStatus.explicit_idle_count },
          { name: '未分配但仍使用中', value: resourceStatus.unassigned_active_count },
          { name: '即将到期', value: resourceStatus.counts.EXPIRING_SOON || 0 },
          { name: '已到期', value: resourceStatus.counts.EXPIRED || 0 },
          { name: '已停用', value: resourceStatus.counts.DISABLED || 0 },
        ]"
      >
        <el-table-column prop="name" label="状态" />
        <el-table-column prop="value" label="数量" width="88" align="right" />
      </el-table>
      <el-table :data="expiring" empty-text="当前没有即将到期资源">
        <el-table-column label="资源" min-width="180">
          <template #default="{ row }">
            <button class="linkish" type="button" @click="goResource(row.id)">{{ row.resource_name }}</button>
          </template>
        </el-table-column>
        <el-table-column prop="expires_at" label="到期日" width="120" />
        <el-table-column prop="days_remaining" label="剩余天数" width="100" align="right" />
      </el-table>
    </section>
  </section>
</template>

<style scoped>
.stats-page {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
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
}

.linkish {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--color-link);
  cursor: pointer;
  font: inherit;
}
</style>
