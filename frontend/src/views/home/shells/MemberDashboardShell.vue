<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import type { Project } from "../../../api/projects";
import type { ResourceStatus, ResourceStatusBrief, ResourceTypeCostItem } from "../../../api/statistics";
import IbmChart, { type ChartSeries } from "../../../components/charts/IbmChart.vue";
import KpiStrip, { type KpiItem } from "../../../components/KpiStrip.vue";
import MoneyText from "../../../components/MoneyText.vue";
import PageHeader from "../../../components/PageHeader.vue";
import StatusTag from "../../../components/StatusTag.vue";
import type { RangePreset } from "../../../utils/dateRange";
import DashboardDateFilter from "../components/DashboardDateFilter.vue";
import ResourceStatusBars from "../components/ResourceStatusBars.vue";

const preset = defineModel<RangePreset>("preset", { required: true });
const customFrom = defineModel<string>("customFrom", { required: true });
const customTo = defineModel<string>("customTo", { required: true });
const props = defineProps<{
  title: string; kpiItems: KpiItem[]; projects: Project[]; trendCategories: string[]; trendSeries: ChartSeries[];
  typeCosts: ResourceTypeCostItem[]; resourceStatus: ResourceStatus | null; expiring: ResourceStatusBrief[];
}>();
const router = useRouter();
const totalsByCurrency = computed(() => props.typeCosts.reduce<Record<string, number>>((totals, item) => {
  totals[item.currency] = (totals[item.currency] || 0) + Number(item.allocated_amount || 0);
  return totals;
}, {}));
function share(row: ResourceTypeCostItem): string {
  const total = totalsByCurrency.value[row.currency] || 0;
  return total ? `${((Number(row.allocated_amount) / total) * 100).toFixed(1)}%` : "-";
}
const goProject = (id: number) => void router.push({ name: "project-detail", params: { id: String(id) } });
const goResource = (id: number) => void router.push({ name: "resource-detail", params: { id: String(id) } });
</script>

<template>
  <section class="dashboard" data-dashboard="member">
    <PageHeader :title="title" />
    <DashboardDateFilter v-model:preset="preset" v-model:custom-from="customFrom" v-model:custom-to="customTo" />
    <KpiStrip :items="kpiItems" :columns="4" />
    <section class="panel"><h2 class="panel__title">我的项目</h2><el-table :data="projects" size="small" empty-text="当前没有参与的项目"><el-table-column label="项目名" min-width="160"><template #default="{row}"><button class="linkish" type="button" @click="goProject(row.id)">{{row.name}}</button></template></el-table-column><el-table-column label="状态" width="100"><template #default="{row}"><StatusTag kind="project" :code="row.status" /></template></el-table-column></el-table></section>
    <div class="grid">
      <section class="panel"><h2 class="panel__title">我的资源状态</h2><ResourceStatusBars :status="resourceStatus" dim-zero /></section>
      <section class="panel"><h2 class="panel__title">我的资源类型费用</h2><el-table :data="typeCosts" size="small" empty-text="当前时间范围暂无资源类型费用"><el-table-column prop="resource_type_name" label="资源类型" min-width="120"/><el-table-column label="费用金额" align="right" min-width="160"><template #default="{row}"><MoneyText :currency="row.currency" :amount="row.allocated_amount" /></template></el-table-column><el-table-column label="占比" width="72" align="right"><template #default="{row}">{{share(row)}}</template></el-table-column></el-table></section>
    </div>
    <section class="panel panel--trend"><h2 class="panel__title">我的费用趋势</h2><IbmChart kind="line" :categories="trendCategories" :series="trendSeries" height="200px" empty-title="当前时间范围暂无费用数据" /></section>
    <section class="panel panel--expiry"><h2 class="panel__title">即将到期资源</h2><p v-if="!expiring.length" class="quiet">当前没有即将到期资源。</p><el-table v-else :data="expiring" size="small"><el-table-column label="资源名称" min-width="180"><template #default="{row}"><button class="linkish" type="button" @click="goResource(row.id)">{{row.resource_name}}</button></template></el-table-column><el-table-column prop="resource_type_name" label="类型" min-width="120"/><el-table-column label="状态" width="110"><template #default="{row}"><StatusTag kind="resource" :code="row.status" /></template></el-table-column><el-table-column prop="expires_at" label="到期日期" width="120"/><el-table-column prop="days_remaining" label="剩余天数" width="100" align="right"/></el-table></section>
  </section>
</template>

<style scoped>
.dashboard{min-width:0;display:flex;flex-direction:column;gap:var(--space-4)}.dashboard :deep(.page-header){margin-bottom:0}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--space-4);align-items:stretch}.panel{min-width:0;padding:var(--space-4);border:1px solid var(--color-border);background:var(--color-bg-panel)}.panel--trend{padding-bottom:var(--space-3)}.panel--expiry{padding-top:var(--space-3);padding-bottom:var(--space-3)}.panel__title{margin:0 0 var(--space-3);font-size:16px;font-weight:400;line-height:1.5}.panel--expiry .panel__title{margin-bottom:var(--space-2)}.linkish{padding:0;border:0;background:transparent;color:var(--color-link);cursor:pointer;font:inherit;text-align:left}.linkish:hover{text-decoration:underline;text-underline-offset:2px}.linkish:focus-visible{outline:2px solid var(--color-focus);outline-offset:2px}.quiet{margin:0;color:var(--color-text-secondary);font-size:14px}.dashboard :deep(.el-table .el-table__cell){padding:6px 0}.dashboard :deep(.el-table__empty-block){min-height:48px}@media(max-width:980px){.grid{grid-template-columns:1fr}}
</style>
