import type { Component } from "vue";
import { isRoleCode, type RoleCode } from "../../../config/roleUi";
import AdminDashboardShell from "./AdminDashboardShell.vue";
import BossDashboardShell from "./BossDashboardShell.vue";
import MemberDashboardShell from "./MemberDashboardShell.vue";
import ProjectManagerDashboardShell from "./ProjectManagerDashboardShell.vue";

const DASHBOARD_SHELLS: Record<RoleCode, Component> = {
  ADMIN: AdminDashboardShell,
  BOSS: BossDashboardShell,
  PROJECT_MANAGER: ProjectManagerDashboardShell,
  MEMBER: MemberDashboardShell,
};

export function dashboardShellFor(role: string | null | undefined): Component {
  if (isRoleCode(role)) return DASHBOARD_SHELLS[role];
  return AdminDashboardShell;
}
