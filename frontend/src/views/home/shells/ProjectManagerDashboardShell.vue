<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import type { Project } from "../../../api/projects";
import type { EmployeeCostItem, ProjectCostItem, ProjectPublicCostItem, ResourceStatus, ResourceTypeCostItem } from "../../../api/statistics";
import IbmChart, { type ChartSeries } from "../../../components/charts/IbmChart.vue";
import KpiStrip, { type KpiItem } from "../../../components/KpiStrip.vue";
import MoneyText from "../../../components/MoneyText.vue";
import PageHeader from "../../../components/PageHeader.vue";
import type { RangePreset } from "../../../utils/dateRange";
import DashboardDateFilter from "../components/DashboardDateFilter.vue";
import ResourceStatusBars from "../components/ResourceStatusBars.vue";

const preset = defineModel<RangePreset>("preset", { required: true });
const customFrom = defineModel<string>("customFrom", { required: true });
const customTo = defineModel<string>("customTo", { required: true });
const projectId = defineModel<number | undefined>("projectId", { required: true });
const props = defineProps<{
  title: string; kpiItems: KpiItem[]; projects: Project[]; trendCategories: string[]; trendSeries: ChartSeries[];
  projectCosts: ProjectCostItem[]; typeCosts: ResourceTypeCostItem[]; employeeCosts: EmployeeCostItem[];
  publicCosts: ProjectPublicCostItem[]; resourceStatus: ResourceStatus | null;
}>();
const router = useRouter();
const attentionItems = computed(() => [
  { label: "即将到期", count: props.resourceStatus?.counts.EXPIRING_SOON || 0 },
  { label: "闲置", count: props.resourceStatus?.explicit_idle_count || 0 },
  { label: "未分配", count: props.resourceStatus?.unassigned_active_count || 0 },
].filter((item) => item.count > 0));
const goProject = (id: number) => void router.push({ name: "project-detail", params: { id: String(id) }, query: { tab: "expenses" } });
const goEmployee = (id: number) => void router.push({ name: "expenses", query: { employee_id: String(id) } });
</script>

<template>
  <section class="dashboard" data-dashboard="project-manager">
    <PageHeader :title="title" />
    <div class="toolbar"><DashboardDateFilter v-model:preset="preset" v-model:custom-from="customFrom" v-model:custom-to="customTo" /><el-select v-if="projects.length > 1" v-model="projectId" clearable placeholder="我的负责项目" class="project-select"><el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" /></el-select></div>
    <KpiStrip :items="kpiItems" :columns="5" />
    <div class="grid grid--hero"><section class="panel"><h2 class="panel__title">我的项目费用</h2><IbmChart kind="line" :categories="trendCategories" :series="trendSeries" height="240px" empty-title="当前时间范围暂无费用数据" /></section><section class="panel"><h2 class="panel__title">资源状态</h2><ResourceStatusBars :status="resourceStatus" /></section></div>
    <div class="grid">
      <section class="panel"><h2 class="panel__title">项目费用</h2><el-table :data="projectCosts" size="small" empty-text="当前时间范围暂无项目费用"><el-table-column label="项目名称" min-width="120"><template #default="{row}"><button class="linkish" type="button" @click="goProject(row.project_id)">{{row.project_name}}</button></template></el-table-column><el-table-column label="金额" align="right" min-width="156"><template #default="{row}"><MoneyText :currency="row.currency" :amount="row.allocated_amount" /></template></el-table-column></el-table></section>
      <section class="panel"><h2 class="panel__title">资源类型费用</h2><el-table :data="typeCosts" size="small" empty-text="当前时间范围暂无资源类型费用"><el-table-column prop="resource_type_name" label="资源类型" min-width="120"/><el-table-column label="金额" align="right" min-width="156"><template #default="{row}"><MoneyText :currency="row.currency" :amount="row.allocated_amount" /></template></el-table-column></el-table></section>
    </div>
    <div class="grid">
      <section class="panel"><h2 class="panel__title">项目成员费用</h2><el-table :data="employeeCosts" size="small" empty-text="当前没有成员直接费用"><el-table-column label="成员" min-width="110"><template #default="{row}"><button class="linkish" type="button" @click="goEmployee(row.employee_id)">{{row.employee_name}}</button></template></el-table-column><el-table-column label="金额" align="right" min-width="156"><template #default="{row}"><MoneyText :currency="row.currency" :amount="row.allocated_amount" /></template></el-table-column></el-table></section>
      <section class="panel"><h2 class="panel__title">项目公共费用</h2><el-table :data="publicCosts" size="small" empty-text="当前没有项目公共费用"><el-table-column label="项目" min-width="130"><template #default="{row}"><button class="linkish" type="button" @click="goProject(row.project_id)">{{row.project_name}}</button></template></el-table-column><el-table-column label="金额" align="right" min-width="156"><template #default="{row}"><MoneyText :currency="row.currency" :amount="row.allocated_amount" /></template></el-table-column></el-table><p class="hint">项目公共费用单独列出，不摊入成员。</p></section>
    </div>
    <section class="panel panel--compact"><h2 class="panel__title">资源关注</h2><p v-if="!attentionItems.length" class="quiet">当前暂无即将到期、闲置或未分配资源。</p><div v-else class="attention"><div v-for="item in attentionItems" :key="item.label"><span>{{item.label}}</span><strong>{{item.count}}</strong></div></div></section>
  </section>
</template>

<style scoped>
.dashboard{min-width:0;display:flex;flex-direction:column;gap:var(--space-4)}.dashboard :deep(.page-header){margin-bottom:0}.toolbar{display:flex;align-items:center;justify-content:space-between;gap:var(--space-4)}.project-select{width:220px;flex:0 0 220px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--space-4);align-items:stretch}.grid--hero{grid-template-columns:minmax(0,2fr) minmax(280px,1fr)}.panel{min-width:0;padding:var(--space-4);border:1px solid var(--color-border);background:var(--color-bg-panel)}.panel--compact{padding-top:var(--space-3);padding-bottom:var(--space-3)}.panel__title{margin:0 0 var(--space-3);font-size:16px;font-weight:400;line-height:1.5}.linkish{padding:0;border:0;background:transparent;color:var(--color-link);cursor:pointer;font:inherit;text-align:left}.linkish:hover{text-decoration:underline;text-underline-offset:2px}.linkish:focus-visible{outline:2px solid var(--color-focus);outline-offset:2px}.hint,.quiet{margin:var(--space-2) 0 0;color:var(--color-text-secondary);font-size:12px}.panel--compact .quiet{margin:0}.attention{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-top:1px solid var(--color-border);border-left:1px solid var(--color-border)}.attention>div{display:flex;justify-content:space-between;padding:8px 12px;border-right:1px solid var(--color-border);border-bottom:1px solid var(--color-border);font-size:14px}.attention strong{font-weight:600;font-variant-numeric:tabular-nums}.dashboard :deep(.el-table .el-table__cell){padding:6px 0}.dashboard :deep(.el-table__empty-block){min-height:48px}@media(max-width:980px){.grid,.grid--hero{grid-template-columns:1fr}.toolbar{align-items:flex-start;flex-direction:column}.project-select{width:100%;flex-basis:auto}.attention{grid-template-columns:1fr}}
</style>
