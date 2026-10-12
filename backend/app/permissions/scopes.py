from app.models.enums import DataScope, RoleCode

ROLE_SCOPES: dict[RoleCode, DataScope] = {
    RoleCode.ADMIN: DataScope.GLOBAL,
    RoleCode.BOSS: DataScope.GLOBAL,
    RoleCode.PROJECT_MANAGER: DataScope.MANAGED_PROJECTS,
    RoleCode.MEMBER: DataScope.MEMBER_PROJECTS,
}


def scope_for_role(role_code: str) -> DataScope:
    try:
        role = RoleCode(role_code)
    except ValueError:
        return DataScope.MEMBER_PROJECTS
    return ROLE_SCOPES[role]
