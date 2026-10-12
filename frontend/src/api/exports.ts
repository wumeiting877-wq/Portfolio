import http from "./http";

export const EXPORT_TYPES = [
  { value: "employees", label: "人员", roles: ["ADMIN"] },
  { value: "projects", label: "项目", roles: ["ADMIN", "BOSS", "PROJECT_MANAGER"] },
  { value: "project_members", label: "项目成员", roles: ["ADMIN", "PROJECT_MANAGER"] },
  { value: "resources", label: "资源账号", roles: ["ADMIN", "BOSS", "PROJECT_MANAGER", "MEMBER"] },
  { value: "resource_allocations", label: "资源分配", roles: ["ADMIN", "PROJECT_MANAGER"] },
  { value: "expenses", label: "费用明细", roles: ["ADMIN", "BOSS", "PROJECT_MANAGER", "MEMBER"] },
  { value: "expense_distributions", label: "费用分摊", roles: ["ADMIN", "PROJECT_MANAGER"] },
  { value: "project_costs", label: "项目费用汇总", roles: ["ADMIN", "BOSS", "PROJECT_MANAGER"] },
  { value: "employee_costs", label: "成员费用汇总", roles: ["ADMIN", "BOSS", "PROJECT_MANAGER"] },
  { value: "resource_type_costs", label: "资源类型费用", roles: ["ADMIN", "BOSS"] },
  { value: "expiring_resources", label: "即将到期资源", roles: ["ADMIN", "BOSS", "PROJECT_MANAGER", "MEMBER"] },
  { value: "idle_resources", label: "闲置资源", roles: ["ADMIN", "BOSS"] },
  { value: "audit_logs", label: "审计日志", roles: ["ADMIN"] },
] as const;

export async function downloadExport(
  exportType: string,
  params: { date_from?: string; date_to?: string; project_id?: number; currency?: string },
): Promise<Blob> {
  const response = await http.get(`/api/exports/${exportType}`, {
    params,
    responseType: "blob",
    timeout: 60000,
  });
  return response.data;
}
