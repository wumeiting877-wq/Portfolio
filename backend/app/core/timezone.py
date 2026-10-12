from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_BUSINESS_TIMEZONE = "Asia/Shanghai"


def parse_timezone(name: str | None) -> ZoneInfo:
    value = (name or DEFAULT_BUSINESS_TIMEZONE).strip() or DEFAULT_BUSINESS_TIMEZONE
    try:
        return ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        return ZoneInfo(DEFAULT_BUSINESS_TIMEZONE)


def today_in_timezone(name: str | None) -> date:
    return datetime.now(parse_timezone(name)).date()
