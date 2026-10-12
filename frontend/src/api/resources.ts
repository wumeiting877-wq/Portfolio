import http from "./http";

export type ResourceType = {
  id: number;
  code: string;
  name: string;
  category: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ResourceTypePayload = {
  code: string;
  name: string;
  category: string;
  description?: string;
};

export type ResourceUsageProject = {
  id: number;
  name: string;
  project_code: string;
};

export type Resource = {
  id: number;
  resource_name: string;
  resource_type: {
    id: number;
    code: string;
    name: string;
    category: string;
  };
  provider: string | null;
  account_identifier: string | null;
  plan_name: string | null;
  status: string;
  purchased_at: string | null;
  activated_at: string | null;
  expires_at: string | null;
  remark: string | null;
  is_expiring_soon: boolean;
  is_shared: boolean;
  active_user_count: number;
  active_project_count: number;
  usage_projects: ResourceUsageProject[];
  created_by: number | null;
  created_at: string;
  updated_at: string;
};

export type ResourceListResponse = {
  items: Resource[];
  total: number;
  page: number;
  page_size: number;
};

export type ResourcePayload = {
  resource_type_id: number;
  resource_name: string;
  provider?: string;
  account_identifier?: string;
  plan_name?: string;
  status: string;
  purchased_at?: string | null;
  activated_at?: string | null;
  expires_at?: string | null;
  remark?: string;
};

export type ResourceAllocation = {
  id: number;
  resource_account_id: number;
  project_id: number | null;
  project_name: string | null;
  project_code: string | null;
  employee_id: number | null;
  employee_name: string | null;
  employee_no: string | null;
  allocated_at: string;
  released_at: string | null;
  is_active: boolean;
  remark: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
};

export async function listResourceTypes(params?: { include_inactive?: boolean }): Promise<ResourceType[]> {
  const response = await http.get<ResourceType[]>("/api/resource-types", { params });
  return response.data;
}

export async function createResourceType(payload: ResourceTypePayload): Promise<ResourceType> {
  const response = await http.post<ResourceType>("/api/resource-types", payload);
  return response.data;
}

export async function updateResourceType(
  id: number,
  payload: Partial<Omit<ResourceTypePayload, "code">>,
): Promise<ResourceType> {
  const response = await http.put<ResourceType>(`/api/resource-types/${id}`, payload);
  return response.data;
}

export async function correctResourceTypeCode(
  id: number,
  newCode: string,
): Promise<ResourceType & { related_account_count: number }> {
  const response = await http.patch<ResourceType & { related_account_count: number }>(
    `/api/resource-types/${id}/code`,
    { new_code: newCode },
  );
  return response.data;
}

export async function disableResourceType(id: number): Promise<ResourceType> {
  const response = await http.post<ResourceType>(`/api/resource-types/${id}/disable`);
  return response.data;
}

export async function enableResourceType(id: number): Promise<ResourceType> {
  const response = await http.post<ResourceType>(`/api/resource-types/${id}/enable`);
  return response.data;
}

export async function listResources(params?: {
  keyword?: string;
  resource_type_id?: number;
  category?: string;
  status?: string;
  project_id?: number;
  employee_id?: number;
  expiring_soon?: boolean;
  page?: number;
  page_size?: number;
}): Promise<ResourceListResponse> {
  const response = await http.get<ResourceListResponse>("/api/resources", { params });
  return response.data;
}

export async function getResource(id: number): Promise<Resource> {
  const response = await http.get<Resource>(`/api/resources/${id}`);
  return response.data;
}

export async function createResource(payload: ResourcePayload): Promise<Resource> {
  const response = await http.post<Resource>("/api/resources", payload);
  return response.data;
}

export async function correctResourceName(id: number, newResourceName: string): Promise<Resource> {
  const response = await http.patch<Resource>(`/api/resources/${id}/resource-name`, {
    new_resource_name: newResourceName,
  });
  return response.data;
}

export async function updateResource(
  id: number,
  payload: Partial<Omit<ResourcePayload, "resource_name">>,
): Promise<Resource> {
  const response = await http.put<Resource>(`/api/resources/${id}`, payload);
  return response.data;
}

export async function disableResource(id: number): Promise<Resource> {
  const response = await http.post<Resource>(`/api/resources/${id}/disable`);
  return response.data;
}

export async function enableResource(id: number): Promise<Resource> {
  const response = await http.post<Resource>(`/api/resources/${id}/enable`);
  return response.data;
}

export async function listResourceAllocations(resourceId: number): Promise<ResourceAllocation[]> {
  const response = await http.get<ResourceAllocation[]>(`/api/resources/${resourceId}/allocations`);
  return response.data;
}

export async function addResourceAllocation(
  resourceId: number,
  payload: { project_id?: number | null; employee_id?: number | null; remark?: string },
): Promise<ResourceAllocation> {
  const response = await http.post<ResourceAllocation>(`/api/resources/${resourceId}/allocations`, payload);
  return response.data;
}

export async function releaseResourceAllocation(
  resourceId: number,
  allocationId: number,
): Promise<ResourceAllocation> {
  const response = await http.delete<ResourceAllocation>(
    `/api/resources/${resourceId}/allocations/${allocationId}`,
  );
  return response.data;
}

export async function restoreResourceAllocation(
  resourceId: number,
  allocationId: number,
): Promise<ResourceAllocation> {
  const response = await http.post<ResourceAllocation>(
    `/api/resources/${resourceId}/allocations/${allocationId}/restore`,
  );
  return response.data;
}
