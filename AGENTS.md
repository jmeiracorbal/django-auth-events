# django-auth-events

## what this library does

Django integration for consuming session invalidation events from a Redis Stream and blocking invalidated tokens at the middleware layer. Depends on `django-auth-external` for token validation.

## package structure

```
django_auth_events/
  config.py        — AuthEventsConfig dataclass + _build_config()
  events.py        — SessionInvalidatedEvent
  store.py         — invalidate_user, is_invalidated (Django cache)
  middleware.py    — AuthEventsMiddleware
  management/
    commands/
      consume_auth_events.py  — long-running consumer command
```

<!-- rule:django-settings -->
## settings contract

Required keys (domain — raise `ImproperlyConfigured` if absent):
- `CACHE_KEY_PREFIX`: cache key namespace for invalidation records
- `STREAM`: Redis stream name to consume from
- `GROUP`: Redis consumer group name

Optional keys (technical — defaults are reasonable):
- `CACHE_TTL`: cache entry TTL in seconds (default `86400`)

`REDIS_URL` is read directly from the top-level Django settings (not from `AUTH_EVENTS`) — it is infrastructure shared across the project, not specific to this feature.

```python
AUTH_EVENTS = {
    "CACHE_KEY_PREFIX": "auth_events:invalidated:",
    "STREAM": "auth:session:events",
    "GROUP": "my-service",
    "CACHE_TTL": 86400,
}

REDIS_URL = "redis://redis:6379"
```

<!-- rule:config-injection -->
## config is injected, not read globally

`invalidate_user` and `is_invalidated` in `store.py` receive an `AuthEventsConfig` instance as a parameter. They do not read settings themselves. This keeps the store testable without Django settings overhead.

<!-- rule:domain-no-default -->
## domain values have no defaults

`CACHE_KEY_PREFIX`, `STREAM`, and `GROUP` are domain decisions made by the consuming application. Do not add defaults for them. If they are missing, startup must fail with `ImproperlyConfigured`.
