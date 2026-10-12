from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.timezone import DEFAULT_BUSINESS_TIMEZONE, today_in_timezone
from app.models.enums import CurrencyCode
from app.models.system_settings import SystemSettings
from app.repositories.resource_repository import EXPIRING_SOON_DAYS
from app.schemas.settings import SystemSettingsPublic, SystemSettingsUpdate
from app.services.audit_service import write_audit

SETTINGS_ROW_ID = 1


def _snapshot(row: SystemSettings) -> dict:
    return {
        "company_name": row.company_name,
        "default_currency": row.default_currency,
        "business_timezone": row.business_timezone,
        "expiring_days": row.expiring_days,
        "page_size_default": row.page_size_default,
    }


def _require_timezone(name: str) -> str:
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的时区") from exc
    return name


def get_or_create_settings(db: Session) -> SystemSettings:
    row = db.query(SystemSettings).filter(SystemSettings.id == SETTINGS_ROW_ID).first()
    if row is not None:
        return row
    row = SystemSettings(
        id=SETTINGS_ROW_ID,
        company_name="项目费用中枢",
        default_currency=CurrencyCode.CNY.value,
        business_timezone=DEFAULT_BUSINESS_TIMEZONE,
        expiring_days=EXPIRING_SOON_DAYS,
        page_size_default=20,
    )
    db.add(row)
    db.flush()
    return row


def serialize_settings(row: SystemSettings) -> SystemSettingsPublic:
    return SystemSettingsPublic.model_validate(row)


def get_settings_public(db: Session) -> SystemSettingsPublic:
    return serialize_settings(get_or_create_settings(db))


def business_today(db: Session) -> date:
    return today_in_timezone(get_or_create_settings(db).business_timezone)


def get_expiring_days(db: Session) -> int:
    return get_or_create_settings(db).expiring_days


def get_default_currency(db: Session) -> str:
    return get_or_create_settings(db).default_currency


def update_settings(
    db: Session,
    payload: SystemSettingsUpdate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> SystemSettings:
    row = get_or_create_settings(db)
    before = _snapshot(row)
    data = payload.model_dump(exclude_unset=True)
    if "default_currency" in data and data["default_currency"] is not None:
        try:
            data["default_currency"] = CurrencyCode(data["default_currency"]).value
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的币种") from exc
    if "business_timezone" in data and data["business_timezone"] is not None:
        data["business_timezone"] = _require_timezone(data["business_timezone"])
    for key, value in data.items():
        setattr(row, key, value)
    row.updated_by = operator_user_id
    db.add(row)
    db.flush()
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="SETTINGS_UPDATE",
        module="settings",
        target_type="system_settings",
        target_id=row.id,
        before_data=before,
        after_data=_snapshot(row),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(row)
    return row
