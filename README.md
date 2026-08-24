# django-auth-events

[![PyPI version](https://img.shields.io/pypi/v/django-auth-events.svg)](https://pypi.org/project/django-auth-events/)
[![Python](https://img.shields.io/pypi/pyversions/django-auth-events.svg)](https://pypi.org/project/django-auth-events/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/jmeiracorbal/django-auth-events/actions/workflows/tests.yml/badge.svg)](https://github.com/jmeiracorbal/django-auth-events/actions)

Auth session event consumer for Django. Bridges event-driven session invalidation with JWT token validation.

Combines `streambus` (event consumption) with `django-auth-external` (token validation) to reject tokens whose sessions have been explicitly invalidated — without tight coupling between services.

## how it works

One service publishes a `SessionInvalidatedEvent` to an event stream whenever a user's access changes. Each Django service runs `consume_auth_events`, which receives those events and stores the invalidation state in Django's cache. The `AuthEventsMiddleware` checks that state on every request.

Token validation and invalidation are both in the middleware — no Redis dependency in the library itself. The cache backend is whatever you configure in Django's `CACHES` setting.

## install

```bash
pip install django-auth-events
```

## setup

Add the middleware (replaces `AuthExternalMiddleware` from `django-auth-external`):

```python
MIDDLEWARE = [
    ...
    "django_auth_events.middleware.AuthEventsMiddleware",
]
```

Configure auth and event settings:

```python
AUTH_EXTERNAL = {
    "SECRET_KEY": "your-secret-key",
    "CLAIMS": ["user_id", "email"],
}

AUTH_EVENTS = {
    "STREAM": "auth:session:events",
    "GROUP": "my-service",
    "REDIS_URL": "redis://localhost:6379",
    "CACHE_TTL": 86400,
}
```

Configure the cache backend (Redis recommended for multi-process deployments):

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://localhost:6379",
    }
}
```

Run the consumer:

```bash
python manage.py consume_auth_events
```

## events

Publish a `SessionInvalidatedEvent` from any service to invalidate a user's active tokens:

```python
from django_auth_events import SessionInvalidatedEvent
from streambus import EventPublisher
from streambus.transports.redis_streams import RedisStreamsTransport
from streambus.config import RedisConfig

transport = RedisStreamsTransport(RedisConfig(url="redis://localhost:6379"))
publisher = EventPublisher(stream="auth:session:events", transport=transport)
publisher.publish(SessionInvalidatedEvent(event_type="session.invalidated", user_id="abc-123"))
```

## configuration

| Key | Default | Description |
|-----|---------|-------------|
| `STREAM` | `"auth:session:events"` | Redis Stream key to consume from. |
| `GROUP` | `"django-auth-events"` | Consumer group name. Use a unique name per service. |
| `REDIS_URL` | `"redis://localhost:6379"` | Redis URL for the event stream. |
| `CACHE_TTL` | `86400` | Invalidation record TTL in seconds (24 hours). |

## license

MIT
