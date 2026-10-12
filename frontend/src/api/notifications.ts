import http from "./http";

export type NotificationItem = {
  id: number;
  type: string;
  target_type: string;
  target_id: string;
  title: string;
  message: string;
  status: string;
  resource_account_id: number | null;
  resource_name: string | null;
  project_id: number | null;
  project_name: string | null;
  due_date: string | null;
  created_at: string;
  read_at: string | null;
  resolved_at: string | null;
};

export type NotificationList = {
  items: NotificationItem[];
  total: number;
  page: number;
  page_size: number;
  generated?: number;
};

export async function listNotifications(params: {
  status?: string;
  type?: string;
  page?: number;
  page_size?: number;
}): Promise<NotificationList> {
  const response = await http.get<NotificationList>("/api/notifications", { params });
  return response.data;
}

export async function refreshNotifications(): Promise<NotificationList> {
  const response = await http.post<NotificationList>("/api/notifications/refresh");
  return response.data;
}

export async function markNotificationRead(id: number): Promise<NotificationItem> {
  const response = await http.post<NotificationItem>(`/api/notifications/${id}/read`);
  return response.data;
}

export async function markNotificationResolved(id: number): Promise<NotificationItem> {
  const response = await http.post<NotificationItem>(`/api/notifications/${id}/resolve`);
  return response.data;
}
