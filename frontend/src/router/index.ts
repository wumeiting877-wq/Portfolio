import { createRouter, createWebHistory } from "vue-router";
import {
  breadcrumbTrail,
  ROUTE_ROLES,
  type BreadcrumbMetaItem,
  type BusinessRouteName,
} from "../config/roleUi";
import { useAuthStore } from "../stores/auth";

declare module "vue-router" {
  interface RouteMeta {
    public?: boolean;
    roles?: string[];
    title?: string;
    breadcrumb?: BreadcrumbMetaItem[];
  }
}

function routeMeta(name: BusinessRouteName) {
  return {
    roles: [...ROUTE_ROLES[name]],
    breadcrumb: breadcrumbTrail(name),
  };
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: () => import("../views/login/LoginView.vue"),
      meta: { public: true },
    },
    {
      path: "/change-password",
      name: "change-password",
      component: () => import("../views/login/ChangePasswordView.vue"),
    },
    {
      path: "/",
      component: () => import("../layouts/AdminLayout.vue"),
      children: [
        {
          path: "",
          name: "home",
          component: () => import("../views/home/HomeView.vue"),
          meta: routeMeta("home"),
        },
        {
          path: "statistics",
          name: "statistics",
          component: () => import("../views/statistics/StatisticsView.vue"),
          meta: routeMeta("statistics"),
        },
        {
          path: "projects",
          name: "projects",
          component: () => import("../views/projects/ProjectListView.vue"),
          meta: routeMeta("projects"),
        },
        {
          path: "projects/:id",
          name: "project-detail",
          component: () => import("../views/projects/ProjectDetailView.vue"),
          meta: routeMeta("project-detail"),
        },
        {
          path: "resources",
          name: "resources",
          component: () => import("../views/resources/ResourceListView.vue"),
          meta: routeMeta("resources"),
        },
        {
          path: "resources/:id",
          name: "resource-detail",
          component: () => import("../views/resources/ResourceDetailView.vue"),
          meta: routeMeta("resource-detail"),
        },
        {
          path: "expenses",
          name: "expenses",
          component: () => import("../views/expenses/ExpenseListView.vue"),
          meta: routeMeta("expenses"),
        },
        {
          path: "expenses/:id",
          name: "expense-detail",
          component: () => import("../views/expenses/ExpenseDetailView.vue"),
          meta: routeMeta("expense-detail"),
        },
        {
          path: "recurring-expenses",
          name: "recurring-expenses",
          component: () => import("../views/expenses/RecurringExpenseListView.vue"),
          meta: routeMeta("recurring-expenses"),
        },
        {
          path: "employees",
          name: "employees",
          component: () => import("../views/employees/EmployeeListView.vue"),
          meta: routeMeta("employees"),
        },
        {
          path: "users",
          name: "users",
          component: () => import("../views/users/UserListView.vue"),
          meta: routeMeta("users"),
        },
        {
          path: "import-export",
          name: "import-export",
          component: () => import("../views/enterprise/ImportExportView.vue"),
          meta: routeMeta("import-export"),
        },
        {
          path: "notifications",
          name: "notifications",
          component: () => import("../views/enterprise/NotificationsView.vue"),
          meta: routeMeta("notifications"),
        },
        {
          path: "audit-logs",
          name: "audit-logs",
          component: () => import("../views/enterprise/AuditLogsView.vue"),
          meta: routeMeta("audit-logs"),
        },
        {
          path: "settings",
          name: "settings",
          component: () => import("../views/enterprise/SettingsView.vue"),
          meta: routeMeta("settings"),
        },
      ],
    },
  ],
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (to.meta.public) {
    if (auth.token && to.name === "login") {
      return { name: "home" };
    }
    return true;
  }
  if (!auth.token) {
    return { name: "login" };
  }
  if (!auth.profile) {
    try {
      await auth.fetchProfile();
    } catch {
      await auth.logout();
      return { name: "login" };
    }
  }
  if (auth.profile?.must_change_password && to.name !== "change-password") {
    return { name: "change-password" };
  }
  const roles = to.meta.roles as string[] | undefined;
  if (roles && auth.profile && !roles.includes(auth.profile.role)) {
    return { name: "home" };
  }
  return true;
});

export default router;
