from datetime import datetime, timezone

import pytest
from django.core.cache import cache

from django_auth_events.config import _build_config
from django_auth_events.store import invalidate_user, is_invalidated


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def events_config():
    return _build_config()


def test_not_invalidated_by_default(events_config):
    now = datetime.now(timezone.utc)
    assert not is_invalidated("abc", now, events_config)


def test_invalidated_after_invalidate_user(events_config):
    invalidate_user("abc", events_config)
    token_iat = datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert is_invalidated("abc", token_iat, events_config)


def test_token_issued_after_invalidation_is_not_rejected(events_config):
    invalidate_user("abc", events_config)
    token_iat = datetime(2099, 1, 1, tzinfo=timezone.utc)
    assert not is_invalidated("abc", token_iat, events_config)


def test_different_users_are_independent(events_config):
    invalidate_user("abc", events_config)
    token_iat = datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert is_invalidated("abc", token_iat, events_config)
    assert not is_invalidated("xyz", token_iat, events_config)
