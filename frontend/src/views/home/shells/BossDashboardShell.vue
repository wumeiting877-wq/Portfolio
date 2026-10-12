<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import type { BillingCostItem, ProjectCostItem, ResourceStatus, ResourceStatusBrief, ResourceTypeCostItem } from "../../../api/statistics";
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
  title: string; loading: boolean; kpiItems: KpiItem[]; trendCategories: string[]; trendSeries: ChartSeries[];
  projectCosts: ProjectCostItem[]; projectCostsHasMore: boolean; typeCosts: ResourceTypeCostItem[];
  billingCosts: BillingCostItem[]; resourceStatus: ResourceStatus | null; expiring: ResourceStatusBrief[];
}>();

const router = useRouter();
const structureTab = ref<"type" | "billing">("type");
const expiringCount = computed(() => props.resourceStatus?.counts.EXPIRING_SOON || 0);
const idleCount = computed(() => props.resourceStatus?.explicit_idle_count || 0);
const unassignedCount = computed(() => props.resourceStatus?.unassigned_active_count || 0);
const hasAttention = computed(() => expiringCount.value > 0 || idleCount.value > 0 || unassignedCount.value > 0);
const goProject = (id: number) => void router.push({ name: "project-detail", params: { id: String(id) }, query: { tab: "expenses" } });
const goResource = (id: number) => void router.push({ name: "resource-detail", params: { id: String(id) } });
const goStatistics = () => void router.push({ name: "statistics" });
</script>

<template>
  <section class="dashboard" data-dashboard="boss">
    <PageHeader :title="title" />
    <DashboardDateFilter v-model:preset="preset" v-model:custom-from="customFrom" v-model:custom-to="customTo" />
    <KpiStrip :items="kpiItems" :columns="5" />
    <div class="grid grid--hero">
      <section class="panel"><h2 class="panel__title">费用趋势</h2><IbmChart kind="line" :categories="trendCategories" :series="trendSeries" height="240px" empty-title="当前时间范围暂无费用数据" /></section>
      <section class="panel"><h2 class="panel__title">资源状态</h2><ResourceStatusBars :status="resourceStatus" /></section>
    </div>
    <div class="grid">
      <section class="panel">
        <div class="panel__head"><h2 class="panel__title">项目成本</h2><button v-if="projectCostsHasMore" class="linkish" type="button" @click="goStatistics">查看全部</button></div>
        <el-table :data="projectCosts" size="small" empty-text="当前时间范围暂无项目费用">
          <el-table-column label="项目名称" min-width="140"><template #default="{ row }"><button class="linkish" type="button" @click="goProject(row.project_id)">{{ row.project_name }}</button></template></el-table-column>
          <el-table-column label="费用金额" align="right" min-width="168"><template #default="{ row }"><MoneyText :currency="row.currency" :amount="row.allocated_amount" /></template></el-table-column>
        </el-table>
      </section>
      <section class="panel">
        <h2 class="panel__title">费用结构</h2>
        <div class="tabs" role="tablist" aria-label="费用结构维度"><button class="tab" :class="{ 'is-selected': structureTab === 'type' }" type="button" role="tab" :aria-selected="structureTab === 'type'" @click="structureTab = 'type'">按资源类型</button><button class="tab" :class="{ 'is-selected': structureTab === 'billing' }" type="button" role="tab" :aria-selected="structureTab === 'billing'" @click="structureTab = 'billing'">按计费方式</button></div>
        <el-table v-if="structureTab === 'type'" :data="typeCosts" size="small" empty-text="当前时间范围暂无资源类型费用">
          <el-table-column prop="resource_type_name" label="资源类型" min-width="130" /><el-table-column label="金额" align="right" min-width="168"><template #default="{ row }"><MoneyText :currency="row.currency" :amount="row.allocated_amount" /></template></el-table-column>
        </el-table>
        <el-table v-else :data="billingCosts" size="small" empty-text="当前时间范围暂无计费方式费用">
          <el-table-column label="计费方式" min-width="120"><template #default="{ row }"><StatusTag kind="billing" :code="row.billing_mode" /></template></el-table-column><el-table-column prop="category" label="类别" min-width="100" /><el-table-column label="金额" align="right" min-width="168"><template #default="{ row }"><MoneyText :currency="row.currency" :amount="row.allocated_amount" /></template></el-table-column>
        </el-table>
      </section>
    </div>
    <section class="panel">
      <h2 class="panel__title">需要关注</h2>
      <p v-if="!loading && resourceStatus && !hasAttention" class="quiet">当前暂无需要关注的资源事项</p>
      <div v-else-if="hasAttention" class="attention-grid">
        <div v-if="expiringCount" class="attention-block"><div class="attention-heading"><span>即将到期</span><strong>{{ expiringCount }}</strong></div><p class="attention-note">30 天内到期</p><ul><li v-for="item in expiring" :key="item.id"><button class="linkish" type="button" @click="goResource(item.id)">{{ item.resource_name }}</button><time :datetime="item.expires_at || undefined">{{ item.expires_at || "-" }}</time></li></ul></div>
        <div v-if="unassignedCount" class="attention-block"><div class="attention-heading"><span>尚未分配</span><strong>{{ unassignedCount }}</strong></div><p class="attention-note">使用中资源</p><ul><li v-for="item in resourceStatus?.unassigned_active_resources" :key="item.id"><button class="linkish" type="button" @click="goResource(item.id)">{{ item.resource_name }}</button></li></ul></div>
        <div v-if="idleCount" class="attention-block"><div class="attention-heading"><span>闲置</span><strong>{{ idleCount }}</strong></div><p class="attention-note">当前闲置资源</p><ul><li v-for="item in resourceStatus?.idle_resources" :key="item.id"><button class="linkish" type="button" @click="goResource(item.id)">{{ item.resource_name }}</button></li></ul></div>
      </div>
    </section>
  </section>
</template>

<style scoped>
.dashboard{min-width:0;display:flex;flex-direction:column;gap:var(--space-4)}.dashboard :deep(.page-header){margin-bottom:0}.grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:var(--space-4);align-items:stretch}.grid--hero{grid-template-columns:minmax(0,2fr) minmax(280px,1fr)}.panel{min-width:0;padding:var(--space-4);border:1px solid var(--color-border);background:var(--color-bg-panel)}.panel__head{display:flex;align-items:baseline;justify-content:space-between;gap:var(--space-3)}.panel__title{margin:0 0 var(--space-3);color:var(--color-text-primary);font-size:16px;font-weight:400;line-height:1.5;letter-spacing:.16px}.linkish{padding:0;border:0;background:transparent;color:var(--color-link);cursor:pointer;font:inherit;text-align:left}.linkish:hover{text-decoration:underline;text-underline-offset:2px}.linkish:focus-visible{outline:2px solid var(--color-focus);outline-offset:2px}.tabs{display:flex;margin:calc(var(--space-2)*-1) 0 var(--space-3);border-bottom:1px solid var(--color-border)}.tab{min-height:40px;padding:10px 16px;border:0;border-radius:0;background:transparent;color:var(--color-text-secondary);cursor:pointer}.tab:hover{color:var(--color-link)}.tab:focus-visible{outline:2px solid var(--color-focus);outline-offset:-2px}.tab.is-selected{color:var(--color-text-primary);font-weight:600;box-shadow:inset 0 -2px var(--color-primary)}.quiet{margin:0;color:var(--color-text-secondary);font-size:14px}.attention-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-top:1px solid var(--color-border);border-left:1px solid var(--color-border)}.attention-block{min-width:0;padding:var(--space-3);border-right:1px solid var(--color-border);border-bottom:1px solid var(--color-border)}.attention-heading{display:flex;align-items:baseline;justify-content:space-between;gap:var(--space-2);font-size:14px}.attention-heading strong{font-size:20px;font-weight:400;font-variant-numeric:tabular-nums}.attention-note{margin:2px 0 0;color:var(--color-text-muted);font-size:12px}.attention-block ul{margin:var(--space-2) 0 0;padding:0;list-style:none}.attention-block li{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:var(--space-3);align-items:baseline;padding:4px 0;color:var(--color-text-secondary);font-size:12px}.attention-block time{white-space:nowrap;font-variant-numeric:tabular-nums}.dashboard :deep(.el-table .el-table__cell){padding:6px 0}.dashboard :deep(.el-table__empty-block){min-height:48px}@media(max-width:980px){.grid,.grid--hero,.attention-grid{grid-template-columns:1fr}}
</style>
