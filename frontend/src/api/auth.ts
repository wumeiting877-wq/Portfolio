import http from "./http";

export type EmployeeBrief = {
  id: number;
  employee_no: string;
  name: string;
  department?: string | null;
  employment_status: string;
};

export type UserPublic = {
  id: number;
  username: string;
  employee_id: number | null;
  role_id: number;
  role_code: string;
  role_name: string;
  status: string;
  must_change_password: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
  employee: EmployeeBrief | null;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  must_change_password: boolean;
  user: UserPublic;
};

export type MeResponse = {
  id: number;
  username: string;
  role: string;
  role_name: string;
  scope: string;
  status: string;
  must_change_password: boolean;
  employee_id: number | null;
  employee_name: string | null;
};

export async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await http.post<LoginResponse>("/api/auth/login", { username, password });
  return response.data;
}

export async function fetchMe(): Promise<MeResponse> {
  const response = await http.get<MeResponse>("/api/auth/me");
  return response.data;
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  await http.post("/api/auth/change-password", {
    old_password: oldPassword,
    new_password: newPassword,
  });
}

export async function logout(): Promise<void> {
  await http.post("/api/auth/logout");
}
