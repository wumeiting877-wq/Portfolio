export const ROLE_CODES = ["ADMIN", "BOSS", "PROJECT_MANAGER", "MEMBER"] as const;

export type RoleCode = (typeof ROLE_CODES)[number];

export const BUSINESS_ROUTE_NAMES = [
  "home",
  "statistics",
  "projects",
  "project-detail",
  "resources",
  "resource-detail",
  "expenses",
  "expense-detail",
  "recurring-expenses",
  "employees",
  "users",
  "import-export",
  "notifications",
  "audit-logs",
  "settings",
] as const;

export type BusinessRouteName = (typeof BUSINESS_ROUTE_NAMES)[number];

export type MenuItemConfig = {
  routeName: BusinessRouteName;
  path: string;
};

export type RoleUiConfig = {
  dashboardTitle: string;
  homeMenuLabel: string;
  breadcrumbRootLabel: string;
  routeLabels: Partial<Record<BusinessRouteName, string>>;
  menuItems: MenuItemConfig[];
};

export type BreadcrumbMetaItem = {
  kind: "root" | "route";
  routeName?: BusinessRouteName;
  to?: { name: string };
};

export type ResolvedMenuItem = {
  path: string;
  label: string;
};

const ALL_ROLES: readonly RoleCode[] = ROLE_CODES;
const ADMIN_BOSS: readonly RoleCode[] = ["ADMIN", "BOSS"];

/** Frontend route UX policy. Backend scope remains the security boundary. */
export const ROUTE_ROLES: Record<BusinessRouteName, readonly RoleCode[]> = {
  home: ALL_ROLES,
  statistics: ALL_ROLES,
  projects: ALL_ROLES,
  "project-detail": ALL_ROLES,
  resources: ALL_ROLES,
  "resource-detail": ALL_ROLES,
  expenses: ALL_ROLES,
  "expense-detail": ALL_ROLES,
  "recurring-expenses": ADMIN_BOSS,
  employees: ADMIN_BOSS,
  users: ["ADMIN"],
  "import-export": ALL_ROLES,
  notifications: ALL_ROLES,
  "audit-logs": ADMIN_BOSS,
  settings: ["ADMIN"],
};

const ROUTE_PATHS: Record<
  Exclude<BusinessRouteName, "project-detail" | "resource-detail" | "expense-detail">,
  string
> = {
  home: "/",
  statistics: "/statistics",
  projects: "/projects",
  resources: "/resources",
  expenses: "/expenses",
  "recurring-expenses": "/recurring-expenses",
  employees: "/employees",
  users: "/users",
  "import-export": "/import-export",
  notifications: "/notifications",
  "audit-logs": "/audit-logs",
  settings: "/settings",
};

const DETAIL_PARENT: Partial<Record<BusinessRouteName, BusinessRouteName>> = {
  "project-detail": "projects",
  "resource-detail": "resources",
  "expense-detail": "expenses",
};

const DETAIL_LABELS: Partial<Record<BusinessRouteName, string>> = {
  "project-detail": "项目详情",
  "resource-detail": "资源详情",
  "expense-detail": "费用详情",
  notifications: "提醒中心",
};

const ENTERPRISE_LABELS: Partial<Record<BusinessRouteName, string>> = {
  "recurring-expenses": "周期规则",
  employees: "人员管理",
  users: "系统账号",
  "audit-logs": "审计日志",
  settings: "系统设置",
};

function menu(routeNames: Array<keyof typeof ROUTE_PATHS>): MenuItemConfig[] {
  return routeNames.map((routeName) => ({
    routeName,
    path: ROUTE_PATHS[routeName],
  }));
}

export const ROLE_UI: Record<RoleCode, RoleUiConfig> = {
  ADMIN: {
    dashboardTitle: "系统管理看板",
    homeMenuLabel: "系统管理看板",
    breadcrumbRootLabel: "首页",
    routeLabels: {
      ...DETAIL_LABELS,
      ...ENTERPRISE_LABELS,
      statistics: "统计分析",
      projects: "项目管理",
      resources: "资源账号",
      expenses: "费用管理",
      "import-export": "导入导出",
    },
    menuItems: menu([
      "home",
      "statistics",
      "projects",
      "resources",
      "expenses",
      "recurring-expenses",
      "employees",
      "users",
      "import-export",
      "notifications",
      "audit-logs",
      "settings",
    ]),
  },
  BOSS: {
    dashboardTitle: "经营总览",
    homeMenuLabel: "经营总览",
    breadcrumbRootLabel: "首页",
    routeLabels: {
      ...DETAIL_LABELS,
      ...ENTERPRISE_LABELS,
      statistics: "统计分析",
      projects: "项目管理",
      resources: "资源账号",
      expenses: "费用管理",
      "import-export": "数据导出",
    },
    menuItems: menu([
      "home",
      "statistics",
      "projects",
      "resources",
      "expenses",
      "recurring-expenses",
      "employees",
      "import-export",
      "notifications",
      "audit-logs",
    ]),
  },
  PROJECT_MANAGER: {
    dashboardTitle: "项目看板",
    homeMenuLabel: "项目看板",
    breadcrumbRootLabel: "首页",
    routeLabels: {
      ...DETAIL_LABELS,
      statistics: "项目统计",
      projects: "我的项目",
      resources: "项目资源",
      expenses: "项目费用",
      "import-export": "数据导出",
    },
    menuItems: menu([
      "home",
      "statistics",
      "projects",
      "resources",
      "expenses",
      "import-export",
      "notifications",
    ]),
  },
  MEMBER: {
    dashboardTitle: "我的资源",
    homeMenuLabel: "我的工作台",
    breadcrumbRootLabel: "首页",
    routeLabels: {
      ...DETAIL_LABELS,
      statistics: "我的统计",
      projects: "我的项目",
      resources: "我的资源",
      expenses: "我的费用",
      "import-export": "数据导出",
    },
    menuItems: menu([
      "home",
      "statistics",
      "projects",
      "resources",
      "expenses",
      "import-export",
      "notifications",
    ]),
  },
};

export function isRoleCode(value: string | null | undefined): value is RoleCode {
  return ROLE_CODES.some((role) => role === value);
}

export function roleUiFor(role: string | null | undefined): RoleUiConfig | null {
  return isRoleCode(role) ? ROLE_UI[role] : null;
}

export function routeLabel(role: string | null | undefined, routeName: string): string {
  const ui = roleUiFor(role);
  if (!ui) return "";
  if (routeName === "home") return ui.dashboardTitle;
  return ui.routeLabels[routeName as BusinessRouteName] ?? "";
}

export function menuItemsFor(role: string | null | undefined): ResolvedMenuItem[] {
  const ui = roleUiFor(role);
  if (!ui) return [];
  return ui.menuItems.map((item) => ({
    path: item.path,
    label: item.routeName === "home" ? ui.homeMenuLabel : (ui.routeLabels[item.routeName] ?? ""),
  }));
}

export function breadcrumbTrail(current: BusinessRouteName): BreadcrumbMetaItem[] {
  const items: BreadcrumbMetaItem[] = [{ kind: "root", to: { name: "home" } }];
  const parent = DETAIL_PARENT[current];
  if (parent) {
    items.push({ kind: "route", routeName: parent, to: { name: parent } });
  }
  items.push({ kind: "route", routeName: current });
  return items;
}

export function breadcrumbTitle(role: string | null | undefined, item: BreadcrumbMetaItem): string {
  if (item.kind === "root") {
    return roleUiFor(role)?.breadcrumbRootLabel ?? "首页";
  }
  return item.routeName ? routeLabel(role, item.routeName) : "";
}
