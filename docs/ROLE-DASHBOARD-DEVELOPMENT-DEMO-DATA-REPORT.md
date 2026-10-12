# Role Dashboard Development Demo Data Report

## 1. Target Environment

- Target environment: `DEVELOPMENT`
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8010`
- PostgreSQL host: `127.0.0.1`
- PostgreSQL published port: `55432`
- Compose health at final verification: backend healthy, PostgreSQL healthy, frontend running.
- No Dashboard UI, CSS, role UI, API, permission, scope, JWT, currency, or statistics implementation was changed.

## 2. Target Database

- Database: `project_cost_hub`
- The seed has hard guards for development, the exact database name, a local host, and port `55432`.
- A connected-database check verifies `current_database()` before every mutation.
- `project_cost_hub_pilot`, port `55433`, backend `8011`, and frontend `5174` were not targeted.

## 3. Seed Method

- Script: `backend/scripts/seed_dashboard_demo.py`
- Supported actions: `--dry-run`, `--apply`, `--verify`, and `--cleanup`.
- All business fixture identifiers use the `DASH-DEMO-` prefix. The explicitly requested login usernames are the only naming exception.
- Months are generated dynamically from the business date/timezone.
- Statistics are produced through real `Project`, `ProjectMember`, `ResourceAccount`, `ResourceAllocation`, `ExpenseRecord`, and `ExpenseDistribution` rows.
- No statistics result/cache rows are created.

## 4. Demo Accounts

| Account | Role | Employee |
| --- | --- | --- |
| `demo_boss` | `BOSS` | `DASH-DEMO-EMP-BOSS` |
| `demo_pm_a` | `PROJECT_MANAGER` | `DASH-DEMO-EMP-PMA` |
| `demo_pm_b` | `PROJECT_MANAGER` | `DASH-DEMO-EMP-PMB` |
| `demo_member_a` | `MEMBER` | `DASH-DEMO-EMP-MA` |
| `demo_member_b` | `MEMBER` | `DASH-DEMO-EMP-MB` |

Passwords are intentionally omitted from this report.

## 5. BOSS Coverage

- Five KPI: PASS.
- Six-month total: CNY `39,716.50`, USD `300.00` in the final service verification window.
- Project count is populated; at least three projects have costs.
- Resource types/cost structure contains at least three populated categories.
- Resource status result: ACTIVE `19`, IDLE `2`, EXPIRED `1`, DISABLED `1`, EXPIRING_SOON `3`, UNASSIGNED_ACTIVE `5` (includes existing development data plus Demo data).
- Attention result: expiring `3`, unassigned `5`, idle `2`.

## 6. PM-A Project A

- Project: `DASH-DEMO-PRJ-A` / `Demo Alpha`.
- Six-month totals: CNY `26,100.00`, USD `200.00`.
- Four project participants, six scoped resources, member costs, public project costs, multiple resource types, and two expiring resources are populated.
- Resource statuses include ACTIVE, IDLE, EXPIRED, DISABLED, and EXPIRING_SOON.
- All attainable frozen Dashboard modules contain data.

### DEMO DATA GAP

Project A cannot report `UNASSIGNED_ACTIVE > 0` through the current frozen statistics contract. The project filter first restricts resources to rows with an active allocation to Project A, while `UNASSIGNED_ACTIVE` requires the same resource to have zero active allocations. Those predicates cannot both be true.

Per the frozen-baseline rule, the API/statistics/UI was not changed to manufacture this state. This is the only final verification failure.

## 7. PM-A Project B

- Project: `DASH-DEMO-PRJ-B` / `企业协同 Demo Beta`.
- It has fewer members, fewer resources, lower costs, and a smaller resource-type mix than Project A.
- Expiring `0`, idle `0`, unassigned `0`.
- The existing empty-state copy was rendered: `当前暂无即将到期、闲置或未分配资源。`
- Project A → Project B switching displayed fresh Project B totals and the correct empty state; no stale state was observed.

## 8. PM-B Isolation

- `demo_pm_b` sees only `DASH-DEMO-PRJ-C`.
- `demo_pm_a` sees only `DASH-DEMO-PRJ-A` and `DASH-DEMO-PRJ-B` among Demo projects.
- `MANAGED_PROJECTS` isolation: PASS.

## 9. MEMBER-A Coverage

- Participates in Project A and Project B.
- Direct resources: `4`; resource types: at least `2`.
- Six natural months all contain CNY direct expense; three months also contain USD.
- Six-month totals: CNY `14,394.00`, USD `120.00`.
- Expiring resource count: `1`.
- Four KPI, projects, resource status, resource-type costs, trend, and expiring resources: PASS.

## 10. MEMBER-B Empty State

- Participates in Project A.
- Has independent direct allocations and expense distributions.
- Expiring resource count: `0`.
- The existing empty-state copy was rendered: `当前没有即将到期资源。`

## 11. Cross-Member Isolation

- Member-A and Member-B readable direct-resource ID sets are disjoint.
- Direct expense totals are independently scoped.
- Neither member can read the other member's direct allocations/distributions through the frozen MEMBER scope.
- Cross-member isolation: PASS.

## 12. CNY / USD

- BOSS: CNY and USD populated.
- PM-A Project A: CNY and USD populated.
- Member-A: CNY and USD populated.
- Currencies remain separate; no cross-currency addition is performed.

## 13. 6-Month Trend

- Dynamic period at execution: `2026-04` through `2026-09`.
- CNY is present in all six months.
- USD is present in `2026-05`, `2026-07`, and `2026-09`.
- Values vary by month and include short and long currency amounts.

## 14. Resource Status Coverage

- Global coverage: ACTIVE, IDLE, UNASSIGNED_ACTIVE, EXPIRING_SOON, EXPIRED, DISABLED.
- Project A coverage: ACTIVE, IDLE, EXPIRING_SOON, EXPIRED, DISABLED.
- Project A project-scoped UNASSIGNED_ACTIVE is the documented semantic gap above.
- Project B deliberately contains no attention state.

## 15. Seed Idempotency

- Counts before second apply: employees `6`, projects `3`, resources `11`, expense records `18`, distributions `33`.
- Counts after second apply: employees `6`, projects `3`, resources `11`, expense records `18`, distributions `33`.
- Stable identifiers are used for upsert; controlled distribution children are replaced under their stable Demo expense record.
- Idempotency: PASS.

## 16. Cleanup

- `--cleanup` deletes only prefix-owned Demo rows and their direct dependencies; it contains no TRUNCATE, DROP, or unbounded delete.
- Cleanup verification removed: 33 distributions, 18 expense records, 9 allocations, 11 resources, 7 project memberships, 3 projects, 5 users, 6 employees, 5 expense types, and 5 resource types.
- Post-cleanup Demo counts were `0|0|0|0` for employees/projects/resources/expenses.
- `--apply` was immediately rerun and restored the complete final Demo data set.
- Cleanup: PASS.

## 17. Build / Test

- `npm run build`: PASS.
- `vue-tsc -b`: PASS.
- Full backend `pytest -q`: PASS (100%, no failures; one third-party deprecation warning).
- Final development services: frontend running; backend and PostgreSQL healthy.
- Role/Scope verification through the real service layer: PASS except the documented Project A unassigned contradiction.

## 18. Pilot Untouched

- Pilot modified: NO.
- No command targeted the Pilot compose file, Pilot environment, port `55433`, backend `8011`, frontend `5174`, or `project_cost_hub_pilot`.
- No Pilot data was read, written, or cleaned.

## 19. Screenshot Index

All screenshots are `1440 × 1000` and are stored in `artifacts/dashboard-full-demo-2026-09-24/`.

- `boss-dashboard-full-demo.png`
- `pm-dashboard-project-a.png`
- `pm-dashboard-project-b.png`
- `member-dashboard-data.png`
- `member-dashboard-empty-expiring.png`

## 20. Visual Follow-Up Candidates

- No UI changes were made after screenshot review.
- No blocking visual defect was observed in the five acceptance screenshots.
- Data/contract follow-up candidate (not a visual fix): decide whether project-filtered statistics should define project-level unassigned resources differently. This requires an explicit future statistics/API decision and must not be addressed as a Demo-data or CSS change.

## Final Result

```text
DASHBOARD FULL DEMO DATA: FAIL

Development DB:
project_cost_hub

Pilot Modified:
NO

BOSS Full Coverage:
YES

PM Multi Project:
YES

PM Empty Attention:
YES

Member Full Coverage:
YES

Member Empty Expiring:
YES

6 Month Trend:
YES

CNY + USD:
YES

All Resource Statuses:
YES (global); NO for Project A UNASSIGNED_ACTIVE due frozen-query contradiction

Scope Isolation:
YES

Seed Idempotent:
YES

Cleanup Available:
YES
```

The overall result is `FAIL` only because the requested Project A unassigned-resource state cannot be represented by the current frozen statistics semantics. All other requested development Demo-data, scope, empty-state, build, cleanup, and screenshot checks pass.
