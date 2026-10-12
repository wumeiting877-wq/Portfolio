import http from "./http";
import type { UserPublic } from "./auth";

export type Role = {
  id: number;
  code: string;
  name: string;
  description: string | null;
};

export async function listRoles(): Promise<Role[]> {
  const response = await http.get<Role[]>("/api/roles");
  return response.data;
}

export async function listUsers(): Promise<UserPublic[]> {
  const response = await http.get<UserPublic[]>("/api/users");
  return response.data;
}

export async function createUser(payload: {
  username: string;
  password: string;
  role_id: number;
  employee_id?: number | null;
}): Promise<UserPublic> {
  const response = await http.post<UserPublic>("/api/users", payload);
  return response.data;
}

export async function correctUsername(id: number, newUsername: string): Promise<UserPublic> {
  const response = await http.patch<UserPublic>(`/api/users/${id}/username`, {
    new_username: newUsername,
  });
  return response.data;
}

export async function updateUser(
  id: number,
  payload: { role_id?: number; employee_id?: number | null; status?: string },
): Promise<UserPublic> {
  const response = await http.put<UserPublic>(`/api/users/${id}`, payload);
  return response.data;
}

export async function resetUserPassword(id: number, password: string): Promise<UserPublic> {
  const response = await http.post<UserPublic>(`/api/users/${id}/reset-password`, { password });
  return response.data;
}

export async function disableUser(id: number): Promise<UserPublic> {
  const response = await http.post<UserPublic>(`/api/users/${id}/disable`);
  return response.data;
}

export async function enableUser(id: number): Promise<UserPublic> {
  const response = await http.post<UserPublic>(`/api/users/${id}/enable`);
  return response.data;
}
