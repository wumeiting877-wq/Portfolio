import http from "./http";

export type AuditLog = {
  id: number;
  operator_user_id: number | null;
  operator_username: string | null;
  action: string;
  module: string;
  target_type: string | null;
  target_id: string | null;
  summary: string | null;
  before_data: Record<string, unknown> | null;
  after_data: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
};

export type AuditLogList = {
  items: AuditLog[];
  total: number;
  page: number;
  page_size: number;
};

export async function listAuditLogs(params: Record<string, string | number | undefined>): Promise<AuditLogList> {
  const response = await http.get<AuditLogList>("/api/audit-logs", { params });
  return response.data;
}

export async function getAuditLog(id: number): Promise<AuditLog> {
  const response = await http.get<AuditLog>(`/api/audit-logs/${id}`);
  return response.data;
}
