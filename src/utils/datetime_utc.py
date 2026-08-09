from datetime import datetime, timezone, timedelta


def datetime_utc_now() -> datetime:
    """
    Returns the current UTC datetime.
    """
    return datetime.now(timezone.utc)
