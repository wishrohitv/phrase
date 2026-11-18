from collections.abc import Callable

from . import OpensubtitleUnauthorized


def refresh_token_middleware(apiCall: Callable[[]], refreshTokenCall: Callable[[]]):
    max_refresh_attempts = 1
    refresh_attempts = 0
    while True:
        try:
            return apiCall()
        except OpensubtitleUnauthorized as e:  # noqa: F841
            if refresh_attempts >= max_refresh_attempts:
                raise
            refresh_attempts += 1
            refreshTokenCall()
