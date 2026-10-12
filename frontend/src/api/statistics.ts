import http from "./http";

export type AmountsByCurrency = Record<string, string>;

export type StatisticsQuery = {
  date_from?: string;
  date_to?: string;
  project_id?: number;
  employee_id?: number;
  limit?: number;
  days?: number;
};

export type Overview = {
  amounts_by_currency: AmountsByCurrency;
  project_count?: number;
  employee_count?: number;
  resource_count?: number;
  active_resource_count?: number;
  idle_resource_count?: number;
  unassigned_active_resource_count?: number;
  expired_resource_count?: number;
  expiring_soon_count?: number;
  my_project_count?: number;
  my_resource_count?: number;
  my_expiring_resource_count?: number;
};

export type TrendPoint = {
  period: string;
  currency: string;
  amount: string;
};

export type ProjectCostItem = {
  project_id: number;
  project_name: string;
  currency: string;
  allocated_amount: string;
};

export type EmployeeCostItem = {
  employee_id: number;
  employee_name: string;
  employee_no: string | null;
  currency: string;
  allocated_amount: string;
};

export type ProjectPublicCostItem = {
  project_id: number;
  project_name: string;
  currency: string;
  allocated_amount: string;
};

export type ResourceTypeCostItem = {
  resource_type_id: number | null;
  resource_type_code: string;
  resource_type_name: string;
  currency: string;
  allocated_amount: string;
};

export type BillingCostItem = {
  billing_mode: string;
  category: string;
  currency: string;
  allocated_amount: string;
};

export type ResourceStatusBrief = {
  id: number;
  resource_name: string;
  status: string;
  expires_at: string | null;
  resource_type_name: string | null;
  days_remaining: number | null;
};

export type ResourceStatus = {
  counts: Record<string, number>;
  explicit_idle_count: number;
  unassigned_active_count: number;
  idle_resources: ResourceStatusBrief[];
  unassigned_active_resources: ResourceStatusBrief[];
};

function params(query: StatisticsQuery = {}) {
  return query;
}

export async function fetchOverview(query?: StatisticsQuery): Promise<Overview> {
  const response = await http.get<Overview>("/api/statistics/overview", { params: params(query) });
  return response.data;
}

export async function fetchExpenseTrend(query?: StatisticsQuery): Promise<{ series: TrendPoint[] }> {
  const response = await http.get<{ series: TrendPoint[] }>("/api/statistics/expense-trend", {
    params: params(query),
  });
  return response.data;
}

export async function fetchProjectCosts(
  query?: StatisticsQuery,
): Promise<{ items: ProjectCostItem[] }> {
  const response = await http.get<{ items: ProjectCostItem[] }>("/api/statistics/project-costs", {
    params: params(query),
  });
  return response.data;
}

export async function fetchEmployeeCosts(query?: StatisticsQuery): Promise<{
  items: EmployeeCostItem[];
  project_public_costs: ProjectPublicCostItem[];
}> {
  const response = await http.get<{
    items: EmployeeCostItem[];
    project_public_costs: ProjectPublicCostItem[];
  }>("/api/statistics/employee-costs", { params: params(query) });
  return response.data;
}

export async function fetchResourceTypeCosts(
  query?: StatisticsQuery,
): Promise<{ items: ResourceTypeCostItem[] }> {
  const response = await http.get<{ items: ResourceTypeCostItem[] }>("/api/statistics/resource-type-costs", {
    params: params(query),
  });
  return response.data;
}

export async function fetchBillingCosts(query?: StatisticsQuery): Promise<{ items: BillingCostItem[] }> {
  const response = await http.get<{ items: BillingCostItem[] }>("/api/statistics/billing-costs", {
    params: params(query),
  });
  return response.data;
}

export async function fetchResourceStatus(query?: StatisticsQuery): Promise<ResourceStatus> {
  const response = await http.get<ResourceStatus>("/api/statistics/resource-status", {
    params: params(query),
  });
  return response.data;
}

export async function fetchExpiringResources(
  query?: StatisticsQuery,
): Promise<{ days: number; items: ResourceStatusBrief[] }> {
  const response = await http.get<{ days: number; items: ResourceStatusBrief[] }>(
    "/api/statistics/expiring-resources",
    { params: params(query) },
  );
  return response.data;
}
