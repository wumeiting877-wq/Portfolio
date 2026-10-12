<script setup lang="ts">
import { RANGE_OPTIONS, type RangePreset } from "../../../utils/dateRange";

const preset = defineModel<RangePreset>("preset", { required: true });
const customFrom = defineModel<string>("customFrom", { required: true });
const customTo = defineModel<string>("customTo", { required: true });
</script>

<template>
  <div class="date-filter">
    <el-radio-group v-model="preset" size="small">
      <el-radio-button v-for="item in RANGE_OPTIONS" :key="item.value" :value="item.value">
        {{ item.label }}
      </el-radio-button>
    </el-radio-group>
    <template v-if="preset === 'custom'">
      <el-date-picker v-model="customFrom" value-format="YYYY-MM-DD" placeholder="开始日期" />
      <el-date-picker v-model="customTo" value-format="YYYY-MM-DD" placeholder="结束日期" />
    </template>
  </div>
</template>

<style scoped>
.date-filter {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}
</style>
