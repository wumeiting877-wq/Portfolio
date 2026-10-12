import http from "./http";

export type ImportErrorItem = {
  row: number;
  field: string;
  message: string;
};

export type ImportPreview = {
  import_type: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  errors: ImportErrorItem[];
  committed?: boolean;
  created_count?: number;
};

export const IMPORT_TYPES = [
  { value: "employees", label: "人员" },
  { value: "projects", label: "项目" },
  { value: "project_members", label: "项目成员" },
  { value: "resource_types", label: "资源类型" },
  { value: "resources", label: "资源账号" },
  { value: "resource_allocations", label: "资源分配" },
  { value: "expenses", label: "费用记录" },
] as const;

export async function downloadImportTemplate(importType: string): Promise<Blob> {
  const response = await http.get(`/api/imports/templates/${importType}`, {
    responseType: "blob",
    timeout: 30000,
  });
  return response.data;
}

export async function previewImport(importType: string, file: File): Promise<ImportPreview> {
  const form = new FormData();
  form.append("file", file);
  const response = await http.post<ImportPreview>(`/api/imports/${importType}/preview`, form, {
    timeout: 60000,
  });
  return response.data;
}

export async function commitImport(importType: string, file: File): Promise<ImportPreview> {
  const form = new FormData();
  form.append("file", file);
  const response = await http.post<ImportPreview>(`/api/imports/${importType}/commit`, form, {
    timeout: 60000,
  });
  return response.data;
}
