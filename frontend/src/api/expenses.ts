import http from "./http";

export type ExpenseType = {
  id: number;
  code: string;
  name: string;
  category: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ExpenseTypePayload = {
  code: string;
  name: string;
  category: string;
  description?: string;
};

export type ExpenseDistribution = {
  id: number;
  expense_record_id: number;
  project_id: number | null;
  project_name: string | null;
  project_code: string | null;
  employee_id: number | null;
  employee_name: string | null;
  employee_no: string | null;
  allocation_method: string;
  allocation_ratio: string | null;
  allocated_amount: string;
  created_at: string;
  updated_at: string;
};

export type ExpenseDistributionInput = {
  project_id?: number | null;
  employee_id?: number | null;
  allocation_method: string;
  allocation_ratio?: string | null;
  allocated_amount?: string | null;
};

export type Expense = {
  id: number;
  expense_type: {
    id: number;
    code: string;
    name: string;
    category: string;
  };
  resource_account_id: number | null;
  resource_name: string | null;
  billing_mode: string;
  source: string;
  expense_date: string;
  billing_period_start: string | null;
  billing_period_end: string | null;
  amount: string;
  visible_allocated_amount: string;
  original_amount_visible: boolean;
  currency: string;
  usage_quantity: string | null;
  usage_unit: string | null;
  unit_price: string | null;
  description: string | null;
  external_reference: string | null;
  status: string;
  recurring_rule_id: number | null;
  visible_attribution: string | null;
  distributions: ExpenseDistribution[];
  created_by: number | null;
  created_at: string;
  updated_at: string;
};

export type ExpenseListResponse = {
  items: Expense[];
  total: number;
  page: number;
  page_size: number;
};

export type ExpensePayload = {
  expense_type_id: number;
  resource_account_id?: number | null;
  billing_mode: string;
  source?: string;
  expense_date: string;
  billing_period_start?: string | null;
  billing_period_end?: string | null;
  amount: string;
  currency: string;
  usage_quantity?: string | null;
  usage_unit?: string | null;
  unit_price?: string | null;
  description?: string;
  external_reference?: string | null;
  distributions: ExpenseDistributionInput[];
};

export type RecurringRuleDistribution = {
  id: number;
  rule_id: number;
  project_id: number | null;
  project_name: string | null;
  project_code: string | null;
  employee_id: number | null;
  employee_name: string | null;
  employee_no: string | null;
  allocation_method: string;
  allocation_ratio: string | null;
  allocated_amount: string | null;
  created_at: string;
  updated_at: string;
};

export type RecurringRule = {
  id: number;
  name: string;
  expense_type: {
    id: number;
    code: string;
    name: string;
    category: string;
  };
  resource_account_id: number | null;
  resource_name: string | null;
  frequency: string;
  amount: string;
  currency: string;
  start_date: string;
  end_date: string | null;
  next_run_date: string;
  is_active: boolean;
  default_distribution_mode: string;
  description: string | null;
  distributions: RecurringRuleDistribution[];
  created_by: number | null;
  created_at: string;
  updated_at: string;
};

export type RecurringRulePayload = {
  name: string;
  expense_type_id: number;
  resource_account_id?: number | null;
  frequency: string;
  amount: string;
  currency: string;
  start_date: string;
  end_date?: string | null;
  next_run_date?: string | null;
  default_distribution_mode: string;
  description?: string;
  distributions: ExpenseDistributionInput[];
};

export type RecurringGenerateResult = {
  generated_count: number;
  skipped_count: number;
  generated_ids: number[];
};

export type SuggestedDistribution = {
  project_id: number | null;
  project_name: string | null;
  employee_id: number | null;
  employee_name: string | null;
  allocation_method: string;
  allocation_ratio: string | null;
  allocated_amount: string;
};

export async function listExpenseTypes(params?: { include_inactive?: boolean }): Promise<ExpenseType[]> {
  const response = await http.get<ExpenseType[]>("/api/expense-types", { params });
  return response.data;
}

export async function createExpenseType(payload: ExpenseTypePayload): Promise<ExpenseType> {
  const response = await http.post<ExpenseType>("/api/expense-types", payload);
  return response.data;
}

export async function correctExpenseTypeCode(id: number, newCode: string): Promise<ExpenseType> {
  const response = await http.patch<ExpenseType>(`/api/expense-types/${id}/code`, {
    new_code: newCode,
  });
  return response.data;
}

export async function updateExpenseType(
  id: number,
  payload: Partial<ExpenseTypePayload>,
): Promise<ExpenseType> {
  const response = await http.put<ExpenseType>(`/api/expense-types/${id}`, payload);
  return response.data;
}

export async function disableExpenseType(id: number): Promise<ExpenseType> {
  const response = await http.post<ExpenseType>(`/api/expense-types/${id}/disable`);
  return response.data;
}

export async function enableExpenseType(id: number): Promise<ExpenseType> {
  const response = await http.post<ExpenseType>(`/api/expense-types/${id}/enable`);
  return response.data;
}

export async function listExpenses(params?: {
  keyword?: string;
  expense_type_id?: number;
  category?: string;
  billing_mode?: string;
  source?: string;
  resource_account_id?: number;
  project_id?: number;
  employee_id?: number;
  currency?: string;
  date_from?: string;
  date_to?: string;
  billing_period?: string;
  status?: string;
  page?: number;
  page_size?: number;
}): Promise<ExpenseListResponse> {
  const response = await http.get<ExpenseListResponse>("/api/expenses", { params });
  return response.data;
}

export async function getExpense(id: number): Promise<Expense> {
  const response = await http.get<Expense>(`/api/expenses/${id}`);
  return response.data;
}

export async function createExpense(payload: ExpensePayload): Promise<Expense> {
  const response = await http.post<Expense>("/api/expenses", payload);
  return response.data;
}

export async function updateExpense(id: number, payload: Partial<ExpensePayload>): Promise<Expense> {
  const response = await http.put<Expense>(`/api/expenses/${id}`, payload);
  return response.data;
}

export async function voidExpense(id: number): Promise<Expense> {
  const response = await http.post<Expense>(`/api/expenses/${id}/void`);
  return response.data;
}

export async function listSuggestedDistributions(
  resourceAccountId: number,
  amount: string,
): Promise<SuggestedDistribution[]> {
  const response = await http.get<SuggestedDistribution[]>("/api/expenses/suggested-distributions", {
    params: { resource_account_id: resourceAccountId, amount },
  });
  return response.data;
}

export async function listRecurringRules(params?: { include_inactive?: boolean }): Promise<RecurringRule[]> {
  const response = await http.get<RecurringRule[]>("/api/recurring-expense-rules", { params });
  return response.data;
}

export async function getRecurringRule(id: number): Promise<RecurringRule> {
  const response = await http.get<RecurringRule>(`/api/recurring-expense-rules/${id}`);
  return response.data;
}

export async function createRecurringRule(payload: RecurringRulePayload): Promise<RecurringRule> {
  const response = await http.post<RecurringRule>("/api/recurring-expense-rules", payload);
  return response.data;
}

export async function updateRecurringRule(
  id: number,
  payload: Partial<RecurringRulePayload>,
): Promise<RecurringRule> {
  const response = await http.put<RecurringRule>(`/api/recurring-expense-rules/${id}`, payload);
  return response.data;
}

export async function disableRecurringRule(id: number): Promise<RecurringRule> {
  const response = await http.post<RecurringRule>(`/api/recurring-expense-rules/${id}/disable`);
  return response.data;
}

export async function enableRecurringRule(id: number): Promise<RecurringRule> {
  const response = await http.post<RecurringRule>(`/api/recurring-expense-rules/${id}/enable`);
  return response.data;
}

export async function generateRecurringExpenses(): Promise<RecurringGenerateResult> {
  const response = await http.post<RecurringGenerateResult>("/api/expenses/recurring/generate");
  return response.data;
}
