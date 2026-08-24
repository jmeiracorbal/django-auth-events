"""
Full orchestration test.

Chain: generate token -> publish invalidation event -> consumer handles it
-> middleware rejects subsequent requests with that token.
"""
import pytest
from django.core.cache import cache
from django.test import RequestFactory

from django_auth_external import generate_token

from django_auth_events.config import _build_config
from django_auth_events.middleware import AuthEventsMiddleware
from django_auth_events.store import invalidate_user

from tests.fixtures import ConcreteSessionInvalidatedEvent, TOKEN_CONFIG as _TOKEN_CONFIG


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def events_config():
    return _build_config()


def _make_request(token: str):
    return RequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {token}")


def _run_middleware(request):
    AuthEventsMiddleware(lambda req: None)(request)
    return request


def test_valid_token_is_accepted():
    token = generate_token({"user_id": "abc", "email": "x@y.com"}, _TOKEN_CONFIG)
    request = _run_middleware(_make_request(token))
    assert request.auth_payload is not None
    assert request.auth_payload["user_id"] == "abc"


def test_token_rejected_after_session_invalidated(events_config):
    token = generate_token({"user_id": "abc", "email": "x@y.com"}, _TOKEN_CONFIG)

    event = ConcreteSessionInvalidatedEvent(event_type="session.invalidated", user_id="abc")
    invalidate_user(event.identifier, events_config)

    request = _run_middleware(_make_request(token))
    assert request.auth_payload is None


def test_different_user_token_not_affected(events_config):
    token_abc = generate_token({"user_id": "abc", "email": "a@y.com"}, _TOKEN_CONFIG)
    token_xyz = generate_token({"user_id": "xyz", "email": "x@y.com"}, _TOKEN_CONFIG)

    invalidate_user("abc", events_config)

    assert _run_middleware(_make_request(token_abc)).auth_payload is None
    assert _run_middleware(_make_request(token_xyz)).auth_payload is not None


def test_no_token_leaves_payload_none():
    request = RequestFactory().get("/")
    _run_middleware(request)
    assert request.auth_payload is None
