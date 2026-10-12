from enum import Enum


class EmploymentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LEFT = "LEFT"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    LOCKED = "LOCKED"


class RoleCode(str, Enum):
    ADMIN = "ADMIN"
    BOSS = "BOSS"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    MEMBER = "MEMBER"


class DataScope(str, Enum):
    GLOBAL = "GLOBAL"
    MANAGED_PROJECTS = "MANAGED_PROJECTS"
    MEMBER_PROJECTS = "MEMBER_PROJECTS"


class PermissionAction(str, Enum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ProjectStatus(str, Enum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class ProjectMemberRole(str, Enum):
    PROJECT_MANAGER = "PROJECT_MANAGER"
    MEMBER = "MEMBER"


class ResourceTypeCategory(str, Enum):
    AI = "AI"
    DEVELOPMENT = "DEVELOPMENT"
    DESIGN = "DESIGN"
    GIT = "GIT"
    CLOUD_SERVER = "CLOUD_SERVER"
    DATABASE = "DATABASE"
    STORAGE = "STORAGE"
    API = "API"
    DOMAIN = "DOMAIN"
    EMAIL = "EMAIL"
    OFFICE = "OFFICE"
    SAAS = "SAAS"
    OTHER = "OTHER"


class ResourceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    EXPIRED = "EXPIRED"
    DISABLED = "DISABLED"


class CredentialType(str, Enum):
    USERNAME_PASSWORD = "USERNAME_PASSWORD"
    API_KEY = "API_KEY"
    ACCESS_TOKEN = "ACCESS_TOKEN"
    CLIENT_CREDENTIAL = "CLIENT_CREDENTIAL"
    SSH_KEY = "SSH_KEY"
    OTHER = "OTHER"


class CredentialStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    DISABLED = "DISABLED"


class ExpenseCategory(str, Enum):
    SUBSCRIPTION = "SUBSCRIPTION"
    ONE_TIME = "ONE_TIME"
    API_USAGE = "API_USAGE"
    SERVER = "SERVER"
    DOMAIN = "DOMAIN"
    CLOUD_SERVICE = "CLOUD_SERVICE"
    SOFTWARE = "SOFTWARE"
    HARDWARE = "HARDWARE"
    OTHER = "OTHER"


class BillingMode(str, Enum):
    RECURRING = "RECURRING"
    ONE_TIME = "ONE_TIME"
    USAGE = "USAGE"
    MANUAL = "MANUAL"


class ExpenseSource(str, Enum):
    MANUAL = "MANUAL"
    RECURRING_RULE = "RECURRING_RULE"
    IMPORT = "IMPORT"
    API_SYNC = "API_SYNC"


class ExpenseStatus(str, Enum):
    ACTIVE = "ACTIVE"
    VOIDED = "VOIDED"


class AllocationMethod(str, Enum):
    DIRECT = "DIRECT"
    EQUAL = "EQUAL"
    RATIO = "RATIO"
    MANUAL = "MANUAL"


class RecurringFrequency(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class CurrencyCode(str, Enum):
    CNY = "CNY"
    USD = "USD"


class NotificationType(str, Enum):
    RESOURCE_EXPIRING = "RESOURCE_EXPIRING"
    RESOURCE_EXPIRED = "RESOURCE_EXPIRED"
    RESOURCE_UNASSIGNED = "RESOURCE_UNASSIGNED"
    RECURRING_RULE_DUE = "RECURRING_RULE_DUE"


class NotificationStatus(str, Enum):
    UNREAD = "UNREAD"
    READ = "READ"
    RESOLVED = "RESOLVED"
