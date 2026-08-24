"""
Full pipeline integration test.

Publisher -> Redis Stream -> Consumer -> Django cache -> Middleware rejects token.

Uses fakeredis as transport so no real Redis is needed.
"""
import fakeredis
import pytest
from django.core.cache import cache
from django.test import RequestFactory

from django_auth_external import generate_token

from django_auth_events.middleware import AuthEventsMiddleware
from django_auth_events.management.commands.consume_auth_events import Command
from streambus import EventListener, EventPublisher
from streambus.config import RedisConfig
from streambus.transports.redis_streams import RedisStreamsTransport

from tests.fixtures import ConcreteSessionInvalidatedEvent, TOKEN_CONFIG as _TOKEN_CONFIG


STREAM = "auth:session:events"
GROUP = "test-consumer"


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def fake_transport():
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    transport = RedisStreamsTransport(RedisConfig(url="redis://localhost:6379"))
    transport._client = redis_client
    return transport


def _make_request(token: str):
    return RequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {token}")


def _run_middleware(request):
    AuthEventsMiddleware(lambda req: None)(request)
    return request


def test_token_rejected_after_event_published_and_consumed(fake_transport):
    token = generate_token({"user_id": "abc", "email": "x@y.com"}, _TOKEN_CONFIG)

    assert _run_middleware(_make_request(token)).auth_payload is not None

    publisher = EventPublisher(stream=STREAM, transport=fake_transport)
    publisher.publish(ConcreteSessionInvalidatedEvent(event_type="session.invalidated", user_id="abc"))

    cmd = Command()
    listener = EventListener(
        stream=STREAM,
        group=GROUP,
        handler=cmd._on_event,
        event_class=cmd._config.event_class,
        transport=fake_transport,
        block_ms=0,
    )
    fake_transport.ensure_group(STREAM, GROUP)
    processed = listener.process_one_batch()

    assert processed == 1
    assert _run_middleware(_make_request(token)).auth_payload is None


def test_token_for_other_user_still_accepted(fake_transport):
    token_abc = generate_token({"user_id": "abc", "email": "a@y.com"}, _TOKEN_CONFIG)
    token_xyz = generate_token({"user_id": "xyz", "email": "x@y.com"}, _TOKEN_CONFIG)

    publisher = EventPublisher(stream=STREAM, transport=fake_transport)
    publisher.publish(ConcreteSessionInvalidatedEvent(event_type="session.invalidated", user_id="abc"))

    cmd = Command()
    listener = EventListener(
        stream=STREAM,
        group=GROUP,
        handler=cmd._on_event,
        event_class=cmd._config.event_class,
        transport=fake_transport,
        block_ms=0,
    )
    fake_transport.ensure_group(STREAM, GROUP)
    listener.process_one_batch()

    assert _run_middleware(_make_request(token_abc)).auth_payload is None
    assert _run_middleware(_make_request(token_xyz)).auth_payload is not None


def test_no_event_no_invalidation(fake_transport):
    token = generate_token({"user_id": "abc", "email": "x@y.com"}, _TOKEN_CONFIG)

    cmd = Command()
    listener = EventListener(
        stream=STREAM,
        group=GROUP,
        handler=cmd._on_event,
        event_class=cmd._config.event_class,
        transport=fake_transport,
        block_ms=0,
    )
    fake_transport.ensure_group(STREAM, GROUP)
    processed = listener.process_one_batch()

    assert processed == 0
    assert _run_middleware(_make_request(token)).auth_payload is not None
