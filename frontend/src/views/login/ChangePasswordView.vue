<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "../../stores/auth";

const router = useRouter();
const auth = useAuthStore();
const loading = ref(false);
const form = reactive({
  oldPassword: "",
  newPassword: "",
});

async function submit() {
  if (form.newPassword.length < 8) {
    ElMessage.warning("新密码至少 8 位");
    return;
  }
  loading.value = true;
  try {
    await auth.changePassword(form.oldPassword, form.newPassword);
    ElMessage.success("密码已更新");
    await router.push({ name: "home" });
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-panel">
      <h1 class="auth-panel__title">修改密码</h1>
      <el-form class="auth-panel__form" label-width="90px">
        <el-form-item label="原密码">
          <el-input v-model="form.oldPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="form.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">保存</el-button>
          <el-button @click="router.push({ name: 'home' })">返回</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>
