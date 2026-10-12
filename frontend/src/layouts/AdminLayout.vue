<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useBreadcrumb } from "../composables/breadcrumb";
import { menuItemsFor } from "../config/roleUi";
import { useAuthStore } from "../stores/auth";
import { useUserStore } from "../stores/user";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const user = useUserStore();

const roleLabels: Record<string, string> = {
  ADMIN: "管理员",
  BOSS: "老板",
  PROJECT_MANAGER: "负责人",
  MEMBER: "成员",
};

const activeMenu = computed(() => {
  if (route.path.startsWith("/statistics")) return "/statistics";
  if (route.path.startsWith("/projects")) return "/projects";
  if (route.path.startsWith("/resources")) return "/resources";
  if (route.path.startsWith("/recurring-expenses")) return "/recurring-expenses";
  if (route.path.startsWith("/expenses")) return "/expenses";
  if (route.path.startsWith("/employees")) return "/employees";
  if (route.path.startsWith("/import-export")) return "/import-export";
  if (route.path.startsWith("/notifications")) return "/notifications";
  if (route.path.startsWith("/audit-logs")) return "/audit-logs";
  if (route.path.startsWith("/settings")) return "/settings";
  if (route.path.startsWith("/users")) return "/users";
  return "/";
});

const breadcrumbs = useBreadcrumb();
const menuItems = computed(() => menuItemsFor(auth.role));

const roleDisplayName = computed(
  () => auth.profile?.role_name || roleLabels[auth.profile?.role || ""] || "",
);

const showRoleName = computed(
  () => Boolean(roleDisplayName.value) && roleDisplayName.value !== user.displayName,
);

async function handleLogout() {
  await auth.logout();
  await router.push({ name: "login" });
}

function onSelect(index: string) {
  if (route.path !== index) {
    void router.push(index);
  }
}
</script>

<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="brand">项目费用中枢</div>
      <el-menu :key="auth.role" class="navigation" :default-active="activeMenu" @select="onSelect">
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          {{ item.label }}
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container class="workspace">
      <el-header height="48px" class="header">
        <nav class="breadcrumb" aria-label="页面路径">
          <template v-for="(item, index) in breadcrumbs" :key="`${item.title}-${index}`">
            <span v-if="index > 0" class="breadcrumb__sep" aria-hidden="true">/</span>
            <router-link
              v-if="item.to && index < breadcrumbs.length - 1"
              class="breadcrumb__item"
              :to="item.to"
            >
              {{ item.title }}
            </router-link>
            <span
              v-else
              class="breadcrumb__item"
              :class="{ 'is-current': index === breadcrumbs.length - 1 }"
              :aria-current="index === breadcrumbs.length - 1 ? 'page' : undefined"
            >
              {{ item.title }}
            </span>
          </template>
        </nav>
        <div class="header-actions">
          <span v-if="user.displayName" class="user-name">{{ user.displayName }}</span>
          <span v-if="showRoleName" class="role-name">{{ roleDisplayName }}</span>
          <el-button text @click="router.push({ name: 'change-password' })">修改密码</el-button>
          <el-button text @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  --header-height: 48px;
  --sidebar-width: 220px;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.aside {
  position: sticky;
  top: 0;
  align-self: flex-start;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  width: var(--sidebar-width);
  height: 100%;
  max-height: 100%;
  overflow: hidden;
  background: var(--color-bg-panel);
  border-right: 1px solid var(--color-border);
  color: var(--color-text-primary);
}

.brand {
  display: flex;
  flex: 0 0 var(--header-height);
  align-items: center;
  box-sizing: border-box;
  height: var(--header-height);
  padding: 0 20px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 600;
}

.navigation {
  flex: 1 1 auto;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
  border-right: 0;
  background: transparent;
}

.navigation :deep(.el-menu-item) {
  height: 44px;
  padding-left: 20px;
  border-left: 3px solid transparent;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 44px;
}

.navigation :deep(.el-menu-item:hover) {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.navigation :deep(.el-menu-item.is-active) {
  border-left-color: var(--color-primary);
  background: var(--color-bg-selected);
  color: var(--color-text-primary);
  font-weight: 600;
}

.workspace {
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.header {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 0 0 var(--header-height);
  box-sizing: border-box;
  height: var(--header-height);
  padding: 0 var(--space-5);
  background: var(--color-bg-panel);
  border-bottom: 1px solid var(--color-border);
  font-size: 14px;
  line-height: 1.29;
  letter-spacing: 0.16px;
}

.breadcrumb {
  --ink: var(--color-text-primary);
  --muted: var(--color-text-secondary);
  display: flex;
  align-items: center;
  min-width: 0;
  overflow: hidden;
  color: var(--muted);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.29;
  white-space: nowrap;
}

.breadcrumb__item {
  min-width: 0;
  overflow: hidden;
  color: var(--muted);
  font-weight: 400;
  text-decoration: none;
  text-overflow: ellipsis;
}

a.breadcrumb__item {
  flex-shrink: 0;
}

a.breadcrumb__item:hover {
  color: var(--ink);
}

.breadcrumb__item.is-current {
  color: var(--ink);
  font-weight: 600;
}

.breadcrumb__sep {
  flex-shrink: 0;
  margin: 0 var(--space-2);
  color: var(--muted);
  font-weight: 400;
}

.header-actions {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: var(--space-2);
  margin-left: var(--space-4);
}

.user-name {
  color: var(--color-text-primary);
  font-weight: 600;
}

.role-name {
  color: var(--color-text-secondary);
  font-weight: 400;
}

.header-actions :deep(.el-button) {
  min-height: 32px;
  color: var(--color-text-secondary);
}

.header-actions :deep(.el-button:hover) {
  color: var(--color-primary);
}

.main {
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: var(--space-5);
  background: var(--color-bg-page);
}

/* All role Dashboard shells share one full-width, Carbon-aligned content rule. */
.main :deep(.dashboard) {
  box-sizing: border-box;
  width: 100%;
  max-width: var(--dashboard-content-max-width);
  margin: 0;
}
</style>
