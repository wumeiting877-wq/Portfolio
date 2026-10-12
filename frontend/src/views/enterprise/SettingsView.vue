<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { fetchSettings, updateSettings } from "../../api/settings";
import { useAuthStore } from "../../stores/auth";
import PageHeader from "../../components/PageHeader.vue";

const auth = useAuthStore();
const loading = ref(false);
const form = reactive({
  company_name: "",
  default_currency: "CNY",
  business_timezone: "Asia/Shanghai",
  expiring_days: 30,
  page_size_default: 20,
});

async function load() {
  loading.value = true;
  try {
    const data = await fetchSettings();
    form.company_name = data.company_name;
    form.default_currency = data.default_currency;
    form.business_timezone = data.business_timezone;
    form.expiring_days = data.expiring_days;
    form.page_size_default = data.page_size_default;
  } finally {
    loading.value = false;
  }
}

async function save() {
  await updateSettings({ ...form });
  ElMessage.success("设置已保存");
  await load();
}

onMounted(load);
</script>

<template>
  <section>
    <PageHeader title="系统设置" description="公司信息、业务时区、到期天数与默认分页。默认币种仅用于新建费用，不触发汇率换算。" />
    <div class="section-panel" v-loading="loading">
      <h2 class="section-panel__title">基础信息</h2>
      <el-form label-width="120px">
        <el-form-item label="公司名称">
          <el-input v-model="form.company_name" :disabled="!auth.canWriteSettings" />
        </el-form-item>
      </el-form>
    </div>
    <div class="section-panel">
      <h2 class="section-panel__title">时间与币种</h2>
      <el-form label-width="120px">
        <el-form-item label="业务时区">
          <el-input v-model="form.business_timezone" :disabled="!auth.canWriteSettings" />
        </el-form-item>
        <el-form-item label="默认币种">
          <el-select v-model="form.default_currency" :disabled="!auth.canWriteSettings" style="width: 240px">
            <el-option label="人民币" value="CNY" />
            <el-option label="美元" value="USD" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>
    <div class="section-panel">
      <h2 class="section-panel__title">提醒设置</h2>
      <el-form label-width="120px">
        <el-form-item label="到期天数">
          <el-input-number v-model="form.expiring_days" :min="1" :max="365" :disabled="!auth.canWriteSettings" />
        </el-form-item>
      </el-form>
    </div>
    <div class="section-panel">
      <h2 class="section-panel__title">分页</h2>
      <el-form label-width="120px">
        <el-form-item label="默认每页">
          <el-input-number v-model="form.page_size_default" :min="5" :max="100" :disabled="!auth.canWriteSettings" />
        </el-form-item>
      </el-form>
      <el-button v-if="auth.canWriteSettings" type="primary" @click="save">保存</el-button>
    </div>
  </section>
</template>

<style scoped>
.section-panel {
  margin: 0 0 var(--space-4);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-none);
  background: var(--color-bg-panel);
}

.section-panel__title {
  margin: 0 0 var(--space-4);
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.29;
}
</style>
