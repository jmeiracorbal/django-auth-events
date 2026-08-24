from django.conf import settings

from tests.fixtures import ConcreteSessionInvalidatedEvent, token_validator


def pytest_configure(config):
    settings.configure(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
        AUTH_EVENTS={
            "CACHE_KEY_PREFIX": "auth_events:invalidated:",
            "STREAM": "auth:session:events",
            "GROUP": "test-group",
            "SUBJECT_CLAIM": "user_id",
            "EVENT_CLASS": ConcreteSessionInvalidatedEvent,
            "VALIDATOR": token_validator,
            "CACHE_TTL": 86400,
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
        ],
        DATABASES={},
    )
