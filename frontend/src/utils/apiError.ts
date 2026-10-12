export type ApiFieldError = {
  field: string;
  message: string;
};

export type ApiErrorView = {
  message: string;
  fields: ApiFieldError[];
};

type ErrorLike = {
  response?: {
    status?: number;
    data?: {
      detail?: unknown;
    };
  };
  config?: {
    url?: string;
  };
};

const STATUS_TEXT: Record<number, string> = {
  400: "请求无法完成",
  403: "没有权限",
  404: "记录不存在",
  409: "数据冲突",
  422: "请检查填写内容",
  500: "服务暂时不可用",
  502: "服务暂时不可用",
  503: "服务暂时不可用",
};

const REQUIRED_BY_SCOPE: Record<string, Record<string, string>> = {
  employee: {
    employee_no: "请输入工号",
    name: "请输入姓名",
  },
  project: {
    project_code: "请输入项目编码",
    name: "请输入项目名称",
    manager_employee_id: "请选择项目负责人",
    manager_employee_no: "请选择项目负责人",
  },
  resource: {
    resource_name: "请输入资源名称",
    resource_type_id: "请选择资源类型",
    resource_type_code: "请选择资源类型",
  },
  allocation: {
    resource_account_id: "请选择资源",
  },
  expense: {
    expense_type_id: "请选择费用类型",
    expense_type_code: "请选择费用类型",
    billing_mode: "请选择计费方式",
    expense_date: "请选择费用日期",
    amount: "请输入金额",
    currency: "请选择币种",
  },
};

const BUSINESS_FIELDS: Record<string, Array<[RegExp, string]>> = {
  employee: [[/工号已存在/, "employee_no"]],
  project: [
    [/项目编码已存在/, "project_code"],
    [/负责人必须是在职人员/, "manager_employee_id"],
    [/结束日期不能早于开始日期/, "end_date"],
    [/人员不存在/, "manager_employee_id"],
  ],
  resource: [
    [/资源类型已停用|无效的资源类型|资源类型不存在/, "resource_type_id"],
    [/资源名称已存在/, "resource_name"],
  ],
  allocation: [
    [/该成员不属于此项目/, "targets"],
    [/项目与成员至少选择一项|项目和人员至少选择一项/, "targets"],
    [/项目不存在|人员不存在|该分配关系已存在/, "targets"],
    [/资源不存在/, "resource"],
  ],
  expense: [
    [/该成员不属于此项目/, "targets"],
    [/项目与成员至少选择一项|项目和人员至少选择一项/, "targets"],
    [/费用类型已停用|费用类型不存在/, "expense_type_id"],
    [/资源账号不存在|资源不存在/, "resource_account_id"],
    [/无效的币种/, "currency"],
    [/无效的计费方式/, "billing_mode"],
    [/金额不能为负数/, "amount"],
    [/分摊金额合计必须等于费用金额|分摊金额不能为空|按比例分摊必须提供比例|至少需要一条费用归属/, "targets"],
    [/项目不存在|人员不存在/, "targets"],
  ],
};

const CREDENTIAL_FIELD = /password|api_key|secret|token|private_key|credential/i;

function scopeOf(url: string): string {
  if (url.includes("/allocations")) return "allocation";
  if (url.includes("/api/expenses")) return "expense";
  if (url.includes("/api/resources")) return "resource";
  if (url.includes("/api/projects")) return "project";
  if (url.includes("/api/employees")) return "employee";
  return "generic";
}

export function isUnsafeDetail(text: string): boolean {
  return /traceback|sqlalchemy|psycopg|integrityerror|programmingerror|duplicate key|stack trace|exception|select\s|insert\s|update\s|delete\s+from|<html|internal server/i.test(
    text,
  );
}

function isUserFacing(text: string): boolean {
  const trimmed = text.trim();
  if (!trimmed || isUnsafeDetail(trimmed)) return false;
  return /[\u4e00-\u9fff]/.test(trimmed);
}

function statusText(status: number | undefined): string {
  if (status && STATUS_TEXT[status]) return STATUS_TEXT[status];
  return "请求失败";
}

function fieldFromLoc(loc: unknown): string {
  if (!Array.isArray(loc)) return "";
  const names = loc.filter((item) => typeof item === "string" && item !== "body");
  return String(names[names.length - 1] || "");
}

function messageForField(scope: string, field: string, kind: string): string {
  if (CREDENTIAL_FIELD.test(field)) return "不能提交凭据";
  const required = REQUIRED_BY_SCOPE[scope]?.[field];
  if (
    required &&
    (kind === "missing" ||
      kind === "string_too_short" ||
      kind === "too_short" ||
      kind.includes("parsing") ||
      kind === "int_type" ||
      kind === "int_parsing" ||
      kind === "decimal_parsing" ||
      kind === "date_from_datetime_parsing" ||
      kind === "date_parsing")
  ) {
    if (kind.includes("date")) return "日期格式不正确";
    return required;
  }
  if (kind.includes("date")) return "日期格式不正确";
  if (field === "amount" || kind.includes("decimal")) return "请输入金额";
  if (required) return required;
  return "";
}

function fieldsFromDetail(scope: string, detail: unknown): ApiFieldError[] {
  if (!Array.isArray(detail)) return [];
  const fields: ApiFieldError[] = [];
  for (const item of detail) {
    if (!item || typeof item !== "object") continue;
    const row = item as { loc?: unknown; type?: unknown; msg?: unknown };
    const field = fieldFromLoc(row.loc);
    const kind = typeof row.type === "string" ? row.type : "";
    const mapped = messageForField(scope, field, kind);
    if (field && mapped) fields.push({ field, message: mapped });
  }
  return fields;
}

function fieldsFromBusiness(scope: string, detail: string): ApiFieldError[] {
  const rules = BUSINESS_FIELDS[scope] || [];
  const fields: ApiFieldError[] = [];
  for (const [pattern, field] of rules) {
    if (pattern.test(detail)) fields.push({ field, message: detail });
  }
  return fields;
}

export function resolveApiError(error: unknown): ApiErrorView {
  const err = (error || {}) as ErrorLike;
  const status = err.response?.status;
  const url = String(err.config?.url || "");
  const scope = scopeOf(url);
  const detail = err.response?.data?.detail;

  if (typeof detail === "string" && isUserFacing(detail)) {
    return { message: detail.trim(), fields: fieldsFromBusiness(scope, detail.trim()) };
  }

  const fields = fieldsFromDetail(scope, detail);
  if (fields.length) {
    const unique = [...new Set(fields.map((item) => item.message))];
    return { message: unique.join("；"), fields };
  }

  if (!err.response) return { message: "请求失败", fields: [] };
  return { message: statusText(status), fields: [] };
}

export function applyApiFieldErrors(error: unknown, target: Record<string, string>): ApiErrorView {
  const view = resolveApiError(error);
  for (const item of view.fields) {
    if (Object.prototype.hasOwnProperty.call(target, item.field)) {
      target[item.field] = item.message;
    }
  }
  return view;
}
