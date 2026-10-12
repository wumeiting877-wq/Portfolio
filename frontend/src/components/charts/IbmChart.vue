<script setup lang="ts">
import EmptyState from "../EmptyState.vue";
import { formatAmount } from "../../utils/money";
import { CHART_AXIS, CHART_SPLIT, seriesColor } from "./chartTheme";

export type ChartSeries = {
  name: string;
  data: Array<number | null>;
};

const props = withDefaults(
  defineProps<{
    kind?: "line" | "bar";
    categories: string[];
    series: ChartSeries[];
    height?: string;
    emptyTitle: string;
  }>(),
  { kind: "line", height: "220px" },
);

const width = 720;
const chartHeight = 280;
const pad = { l: 108, r: 20, t: 32, b: 36 };

const hasData = () =>
  props.series.some((item) => item.data.some((value) => value != null && Number(value) > 0));

function maxValue(): number {
  const values = props.series.flatMap((item) => item.data.filter((value): value is number => value != null));
  return Math.max(1, ...values);
}

function xAt(index: number, count: number): number {
  const inner = width - pad.l - pad.r;
  if (count <= 1) return pad.l + inner / 2;
  return pad.l + (index / (count - 1)) * inner;
}

function yAt(value: number): number {
  const inner = chartHeight - pad.t - pad.b;
  return pad.t + inner - (value / maxValue()) * inner;
}

function linePoints(data: Array<number | null>): string {
  return data
    .map((value, index) => `${xAt(index, data.length)},${yAt(value || 0)}`)
    .join(" ");
}

function barY(row: number, seriesIndex: number, rowCount: number): number {
  const inner = chartHeight - pad.t - pad.b;
  const rowH = inner / Math.max(rowCount, 1);
  return pad.t + row * rowH + 4 + seriesIndex * 10;
}
</script>

<template>
  <EmptyState v-if="!categories.length || !series.length || !hasData()" :title="emptyTitle" />
  <svg v-else class="ibm-chart" :viewBox="`0 0 ${width} ${chartHeight}`" :style="{ height }" role="img">
    <line
      v-for="tick in 4"
      :key="tick"
      :x1="pad.l"
      :x2="width - pad.r"
      :y1="pad.t + ((chartHeight - pad.t - pad.b) * tick) / 4"
      :y2="pad.t + ((chartHeight - pad.t - pad.b) * tick) / 4"
      :stroke="CHART_SPLIT"
      stroke-width="1"
    />
    <g v-if="kind === 'line'">
      <polyline
        v-for="(item, index) in series"
        :key="item.name"
        fill="none"
        :stroke="seriesColor(index)"
        stroke-width="2"
        :points="linePoints(item.data)"
      />
      <template v-for="(item, sIndex) in series" :key="`${item.name}-d`">
        <circle
          v-for="(value, index) in item.data"
          :key="`${item.name}-${index}`"
          v-show="value != null"
          :cx="xAt(index, item.data.length)"
          :cy="yAt(value || 0)"
          r="3"
          :fill="seriesColor(sIndex)"
        >
          <title>{{ item.name }} · {{ categories[index] }}：{{ value == null ? "暂无数据" : formatAmount(value) }}</title>
        </circle>
      </template>
      <text
        v-for="(label, index) in categories"
        :key="label"
        :x="xAt(index, categories.length)"
        :y="chartHeight - 8"
        :fill="CHART_AXIS"
        font-size="11"
        text-anchor="middle"
      >
        {{ label }}
      </text>
    </g>
    <g v-else>
      <template v-for="(name, row) in categories" :key="name">
        <text :x="8" :y="barY(row, 0, categories.length) + 8" :fill="CHART_AXIS" font-size="11">
          {{ name }}
        </text>
        <rect
          v-for="(item, sIndex) in series"
          :key="`${name}-${item.name}`"
          :x="pad.l"
          :y="barY(row, sIndex, categories.length)"
          :width="((item.data[row] || 0) / maxValue()) * (width - pad.l - pad.r)"
          height="8"
          :fill="seriesColor(sIndex)"
        >
          <title>{{ item.name }} · {{ name }}：{{ item.data[row] == null ? "暂无数据" : formatAmount(item.data[row] as number) }}</title>
        </rect>
      </template>
    </g>
    <g v-for="(item, index) in series" :key="`lg-${item.name}`">
      <rect :x="pad.l + index * 92" y="8" width="10" height="10" :fill="seriesColor(index)" />
      <text :x="pad.l + 14 + index * 92" y="17" :fill="CHART_AXIS" font-size="11">{{ item.name }}</text>
    </g>
  </svg>
</template>

<style scoped>
.ibm-chart {
  display: block;
  width: 100%;
  background: var(--color-bg-panel);
}
</style>
