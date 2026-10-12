import http from "./http";

export type SystemSettings = {
  company_name: string;
  default_currency: string;
  business_timezone: string;
  expiring_days: number;
  page_size_default: number;
  updated_by: number | null;
  updated_at: string | null;
};

export async function fetchSettings(): Promise<SystemSettings> {
  const response = await http.get<SystemSettings>("/api/settings");
  return response.data;
}

export async function updateSettings(payload: Partial<SystemSettings>): Promise<SystemSettings> {
  const response = await http.put<SystemSettings>("/api/settings", payload);
  return response.data;
}
