<script setup lang="ts">
import { formatMoney } from "../utils/money";

defineProps<{
  currency: string;
  amount: string | number;
}>();
</script>

<template>
  <span class="money-text">{{ formatMoney(currency, amount) }}</span>
</template>

<style scoped>
.money-text {
  font-variant-numeric: tabular-nums;
  text-align: right;
  white-space: nowrap;
}
</style>
