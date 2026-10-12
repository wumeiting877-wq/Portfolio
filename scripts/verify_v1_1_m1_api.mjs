import { readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const origin = "http://127.0.0.1:8010";
const env = Object.fromEntries(
  (await readFile(join(root, ".env"), "utf8"))
    .split(/\r?\n/)
    .filter((line) => line && !line.startsWith("#") && line.includes("="))
    .map((line) => {
      const index = line.indexOf("=");
      return [line.slice(0, index).trim(), line.slice(index + 1).trim()];
    }),
);

const demoPassword = env.DASHBOARD_DEMO_PASSWORD || "change_me";
const accountSpecs = {
  admin: [env.INITIAL_ADMIN_USERNAME || "admin", env.INITIAL_ADMIN_PASSWORD || "change_me"],
  boss: ["demo_boss", demoPassword],
  pmA: ["demo_pm_a", demoPassword],
  pmB: ["demo_pm_b", demoPassword],
  memberA: ["demo_member_a", demoPassword],
  memberB: ["demo_member_b", demoPassword],
};

async function request(path, { token, method = "GET", body } = {}) {
  const response = await fetch(`${origin}${path}`, {
    method,
    headers: {
      ...(token ? { authorization: `Bearer ${token}` } : {}),
      ...(body === undefined ? {} : { "content-type": "application/json" }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;
  return { status: response.status, data };
}

async function login(username, password) {
  const result = await request("/api/auth/login", { method: "POST", body: { username, password } });
  if (result.status !== 200) throw new Error(`Login failed for ${username}: ${result.status}`);
  return result.data.access_token;
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const tokens = {};
for (const [name, [username, password]] of Object.entries(accountSpecs)) tokens[name] = await login(username, password);

const report = { scope: {}, forbiddenWrites: {}, stableIdentifiers: {}, importExport: {}, currency: {} };
for (const name of Object.keys(tokens)) {
  const token = tokens[name];
  const [me, projects, resources, expenses, overview, notifications] = await Promise.all([
    request("/api/auth/me", { token }),
    request("/api/projects?page=1&page_size=100", { token }),
    request("/api/resources?page=1&page_size=100", { token }),
    request("/api/expenses?page=1&page_size=100", { token }),
    request("/api/statistics/overview?date_from=2026-04-01&date_to=2026-09-30", { token }),
    request("/api/notifications?page=1&page_size=1", { token }),
  ]);
  for (const [label, result] of Object.entries({ me, projects, resources, expenses, overview, notifications })) {
    assert(result.status === 200, `${name} ${label} expected 200, got ${result.status}`);
  }
  report.scope[name] = {
    role: me.data.role,
    scope: me.data.scope,
    projectIds: projects.data.items.map((item) => item.id),
    projectCodes: projects.data.items.map((item) => item.project_code),
    resourceIds: resources.data.items.map((item) => item.id),
    expenseIds: expenses.data.items.map((item) => item.id),
  };
  report.currency[name] = overview.data.amounts_by_currency;
}

assert(report.scope.boss.scope === "GLOBAL", "BOSS scope mismatch");
assert(report.scope.pmA.scope === "MANAGED_PROJECTS", "PM-A scope mismatch");
assert(report.scope.memberA.scope === "MEMBER_PROJECTS", "Member-A scope mismatch");
assert(report.scope.pmA.projectCodes.includes("DASH-DEMO-PRJ-A") && report.scope.pmA.projectCodes.includes("DASH-DEMO-PRJ-B"), "PM-A project scope incomplete");
assert(report.scope.pmB.projectCodes.length === 1 && report.scope.pmB.projectCodes[0] === "DASH-DEMO-PRJ-C", "PM-B isolation failed");
assert(report.scope.memberA.resourceIds.every((id) => !report.scope.memberB.resourceIds.includes(id)), "Member direct resources overlap");
assert("CNY" in report.currency.boss && "USD" in report.currency.boss, "BOSS currency separation missing");
assert("CNY" in report.currency.pmA && "USD" in report.currency.pmA, "PM currency separation missing");
assert("CNY" in report.currency.memberA && "USD" in report.currency.memberA, "Member currency separation missing");

const safeWriteChecks = [
  ["project.archive", "/api/projects/2147483647/archive", "POST"],
  ["employee.delete", "/api/employees/2147483647", "DELETE"],
  ["resource.disable", "/api/resources/2147483647/disable", "POST"],
  ["expense.void", "/api/expenses/2147483647/void", "POST"],
  ["recurring.disable", "/api/recurring-expense-rules/2147483647/disable", "POST"],
  ["systemUser.disable", "/api/users/2147483647/disable", "POST"],
  ["settings.update", "/api/settings", "PUT", {}],
];
for (const role of ["boss", "pmA", "memberA"]) {
  report.forbiddenWrites[role] = {};
  for (const [label, path, method, body] of safeWriteChecks) {
    const result = await request(path, { token: tokens[role], method, body });
    report.forbiddenWrites[role][label] = result.status;
    assert(result.status === 403, `${role} ${label} expected 403, got ${result.status}`);
  }
}

const adminEmployees = (await request("/api/employees", { token: tokens.admin })).data;
const adminProjects = (await request("/api/projects?page=1&page_size=100", { token: tokens.admin })).data.items;
const adminResourceTypes = (await request("/api/resource-types?include_inactive=true", { token: tokens.admin })).data;
const adminExpenseTypes = (await request("/api/expense-types?include_inactive=true", { token: tokens.admin })).data;
const adminUsers = (await request("/api/users", { token: tokens.admin })).data;
const adminResources = (await request("/api/resources?page=1&page_size=100", { token: tokens.admin })).data.items;
const stableTargets = [
  ["employee_no", `/api/employees/${adminEmployees.find((item) => item.employee_no.startsWith("DASH-DEMO-"))?.id}/employee-no/impact`],
  ["project_code", `/api/projects/${adminProjects.find((item) => item.project_code === "DASH-DEMO-PRJ-A")?.id}/project-code/impact`],
  ["resource_type_code", `/api/resource-types/${adminResourceTypes.find((item) => item.code.startsWith("DASH-DEMO-"))?.id}/code/impact`],
  ["expense_type_code", `/api/expense-types/${adminExpenseTypes.find((item) => item.code.startsWith("DASH-DEMO-"))?.id}/code/impact`],
  ["username", `/api/users/${adminUsers.find((item) => item.username === "demo_member_a")?.id}/username/impact`],
  ["resource_name", `/api/resources/${adminResources.find((item) => item.resource_name.startsWith("DASH-DEMO-"))?.id}/resource-name/impact`],
];
for (const [label, path] of stableTargets) {
  assert(!path.includes("undefined"), `Missing stable identifier target: ${label}`);
  const adminResult = await request(path, { token: tokens.admin });
  const bossResult = await request(path, { token: tokens.boss });
  const pmResult = await request(path, { token: tokens.pmA });
  const memberResult = await request(path, { token: tokens.memberA });
  report.stableIdentifiers[label] = { admin: adminResult.status, boss: bossResult.status, pm: pmResult.status, member: memberResult.status };
  assert(adminResult.status === 200 && bossResult.status === 403 && pmResult.status === 403 && memberResult.status === 403, `Stable identifier guard failed: ${label}`);
}

const importExportChecks = {
  admin: [["importTemplate", "/api/imports/templates/employees", 200], ["employeesExport", "/api/exports/employees", 200]],
  boss: [["importTemplate", "/api/imports/templates/employees", 403], ["resourceTypeCostsExport", "/api/exports/resource_type_costs", 200], ["employeesExport", "/api/exports/employees", 403]],
  pmA: [["importTemplate", "/api/imports/templates/employees", 403], ["projectsExport", "/api/exports/projects", 200], ["idleResourcesExport", "/api/exports/idle_resources", 403]],
  memberA: [["importTemplate", "/api/imports/templates/employees", 403], ["resourcesExport", "/api/exports/resources", 200], ["projectsExport", "/api/exports/projects", 403]],
};
for (const [role, checks] of Object.entries(importExportChecks)) {
  report.importExport[role] = {};
  for (const [label, path, expected] of checks) {
    const result = await request(path, { token: tokens[role] });
    report.importExport[role][label] = result.status;
    assert(result.status === expected, `${role} ${label} expected ${expected}, got ${result.status}`);
  }
}

const output = join(root, "artifacts", "v1.1-m1-final-closure-2026-09-24", "api-verification.json");
await writeFile(output, JSON.stringify(report, null, 2));
console.log(JSON.stringify({ status: "PASS", output, summary: report }, null, 2));
