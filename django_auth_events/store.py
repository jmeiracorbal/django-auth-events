from datetime import datetime, timezone

from django.core.cache import cache

from .config import AuthEventsConfig


def invalidate_user(identifier: str, config: AuthEventsConfig) -> None:
    key = f"{config.cache_key_prefix}{identifier}"
    cache.set(key, datetime.now(timezone.utc).isoformat(), config.cache_ttl)


def is_invalidated(identifier: str, token_iat: datetime, config: AuthEventsConfig) -> bool:
    key = f"{config.cache_key_prefix}{identifier}"
    raw = cache.get(key)
    if not raw:
        return False
    invalidated_at = datetime.fromisoformat(raw)
    return token_iat < invalidated_at
