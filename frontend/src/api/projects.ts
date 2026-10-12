import http from "./http";

export type Project = {
  id: number;
  project_code: string;
  name: string;
  description: string | null;
  manager_employee_id: number;
  manager_name: string | null;
  manager_employee_no: string | null;
  status: string;
  start_date: string | null;
  end_date: string | null;
  member_count: number;
  created_by: number | null;
  created_at: string;
  updated_at: string;
};

export type ProjectListResponse = {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
};

export type ProjectPayload = {
  project_code: string;
  name: string;
  manager_employee_id: number;
  status: string;
  description?: string;
  start_date?: string | null;
  end_date?: string | null;
};

export type ProjectMember = {
  id: number;
  project_id: number;
  employee_id: number;
  employee_no: string | null;
  name: string | null;
  department: string | null;
  position: string | null;
  member_role: string;
  joined_at: string;
  left_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export async function listProjects(params?: {
  keyword?: string;
  status?: string;
  page?: number;
  page_size?: number;
}): Promise<ProjectListResponse> {
  const response = await http.get<ProjectListResponse>("/api/projects", { params });
  return response.data;
}

export async function getProject(id: number): Promise<Project> {
  const response = await http.get<Project>(`/api/projects/${id}`);
  return response.data;
}

export async function createProject(payload: ProjectPayload): Promise<Project> {
  const response = await http.post<Project>("/api/projects", payload);
  return response.data;
}

export async function correctProjectCode(id: number, newProjectCode: string): Promise<Project> {
  const response = await http.patch<Project>(`/api/projects/${id}/project-code`, {
    new_project_code: newProjectCode,
  });
  return response.data;
}

export async function updateProject(id: number, payload: Partial<ProjectPayload>): Promise<Project> {
  const response = await http.put<Project>(`/api/projects/${id}`, payload);
  return response.data;
}

export async function archiveProject(id: number): Promise<Project> {
  const response = await http.post<Project>(`/api/projects/${id}/archive`);
  return response.data;
}

export async function listProjectMembers(projectId: number): Promise<ProjectMember[]> {
  const response = await http.get<ProjectMember[]>(`/api/projects/${projectId}/members`);
  return response.data;
}

export async function addProjectMember(
  projectId: number,
  payload: { employee_id: number; member_role?: string },
): Promise<ProjectMember> {
  const response = await http.post<ProjectMember>(`/api/projects/${projectId}/members`, payload);
  return response.data;
}

export async function removeProjectMember(projectId: number, employeeId: number): Promise<ProjectMember> {
  const response = await http.delete<ProjectMember>(`/api/projects/${projectId}/members/${employeeId}`);
  return response.data;
}
