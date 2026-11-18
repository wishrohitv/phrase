from datetime import datetime, timedelta, timezone


def datetime_utc_now() -> datetime:
    """
    Returns the current UTC datetime.
    """
    return datetime.now(timezone.utc)


def datetime_to_unix(dt: datetime) -> int:
    """
    Convert datetime object to unix timestamp

    Args:
        - dt datetime: Datetime object in UTC timezone
    Returns:
        - int: Unix timestamp (seconds since epoch)
    Raises:
        - ValueError: If datetime object is not in UTC timezone
    """
    return dt.timestamp()


def datetime_from_unix(ts: float) -> datetime:
    """
    Convert unix timestamp to datetime object

    Args:
        - ts int(datetime.timestamp): Unix timestamp (seconds since epoch)
    Returns:
        - datetime: Datetime object in UTC timezone
    """
    return datetime.fromtimestamp(ts, tz=timezone.utc)
