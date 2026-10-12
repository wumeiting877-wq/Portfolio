import http from "./http";

export type Employee = {
  id: number;
  employee_no: string;
  name: string;
  department: string | null;
  position: string | null;
  email: string | null;
  phone: string | null;
  employment_status: string;
  remark: string | null;
  has_account: boolean;
  created_at: string;
  updated_at: string;
};

export type EmployeePayload = {
  employee_no: string;
  name: string;
  department?: string;
  position?: string;
  email?: string;
  phone?: string;
  remark?: string;
  employment_status?: string;
};

export async function listEmployees(params?: {
  q?: string;
  employment_status?: string;
}): Promise<Employee[]> {
  const response = await http.get<Employee[]>("/api/employees", { params });
  return response.data;
}

export async function createEmployee(payload: EmployeePayload): Promise<Employee> {
  const response = await http.post<Employee>("/api/employees", payload);
  return response.data;
}

export async function correctEmployeeNo(id: number, newEmployeeNo: string): Promise<Employee> {
  const response = await http.patch<Employee>(`/api/employees/${id}/employee-no`, {
    new_employee_no: newEmployeeNo,
  });
  return response.data;
}

export async function updateEmployee(id: number, payload: Partial<EmployeePayload>): Promise<Employee> {
  const response = await http.put<Employee>(`/api/employees/${id}`, payload);
  return response.data;
}

export async function disableEmployee(id: number): Promise<Employee> {
  const response = await http.delete<Employee>(`/api/employees/${id}`);
  return response.data;
}
