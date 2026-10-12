from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.audit_logs.router import router as audit_logs_router
from app.api.auth.router import router as auth_router
from app.api.employees.router import router as employees_router
from app.api.expense_types.router import router as expense_types_router
from app.api.expenses.router import router as expenses_router
from app.api.exports.router import router as exports_router
from app.api.health.router import router as health_router
from app.api.imports.router import router as imports_router
from app.api.notifications.router import router as notifications_router
from app.api.projects.router import router as projects_router
from app.api.recurring_expense_rules.router import router as recurring_expense_rules_router
from app.api.resource_types.router import router as resource_types_router
from app.api.resource_credentials.router import router as resource_credentials_router
from app.api.resources.router import allocation_search_router, router as resources_router
from app.api.roles.router import router as roles_router
from app.api.settings.router import router as settings_router
from app.api.statistics.router import router as statistics_router
from app.api.users.router import router as users_router
from app.core.config import settings, validate_runtime_config
from app.core.logging import configure_logging
from app.schemas.enterprise import VersionResponse

configure_logging()
validate_runtime_config(settings)

app = FastAPI(
    title="Project Cost Hub",
    version=settings.APP_VERSION,
    description="Enterprise project resource and cost management system.",
    debug=settings.DEBUG and not settings.is_production,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(employees_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(projects_router)
app.include_router(resource_types_router)
app.include_router(resources_router)
app.include_router(resource_credentials_router)
app.include_router(allocation_search_router)
app.include_router(expense_types_router)
app.include_router(expenses_router)
app.include_router(recurring_expense_rules_router)
app.include_router(statistics_router)
app.include_router(imports_router)
app.include_router(exports_router)
app.include_router(notifications_router)
app.include_router(audit_logs_router)
app.include_router(settings_router)


@app.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    return VersionResponse(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )
