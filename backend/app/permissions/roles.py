from app.models.enums import DataScope, PermissionAction, RoleCode

ROLE_PERMISSIONS: dict[RoleCode, set[PermissionAction]] = {
    RoleCode.ADMIN: {
        PermissionAction.READ,
        PermissionAction.CREATE,
        PermissionAction.UPDATE,
        PermissionAction.DELETE,
    },
    RoleCode.BOSS: {PermissionAction.READ},
    RoleCode.PROJECT_MANAGER: {PermissionAction.READ},
    RoleCode.MEMBER: {PermissionAction.READ},
}


def role_has_permission(role_code: str, action: PermissionAction) -> bool:
    try:
        role = RoleCode(role_code)
    except ValueError:
        return False
    return action in ROLE_PERMISSIONS.get(role, set())
