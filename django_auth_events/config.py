from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


@dataclass
class AuthEventsConfig:
    cache_key_prefix: str
    stream: str
    group: str
    subject_claim: str
    event_class: type
    validator: Callable[[str], dict]
    cache_ttl: int = 86400


def _build_config() -> AuthEventsConfig:
    cfg = getattr(django_settings, "AUTH_EVENTS", {})
    required = ("CACHE_KEY_PREFIX", "STREAM", "GROUP", "SUBJECT_CLAIM", "EVENT_CLASS", "VALIDATOR")
    missing = [k for k in required if k not in cfg]
    if missing:
        raise ImproperlyConfigured(
            f"AUTH_EVENTS is missing required keys: {', '.join(missing)}"
        )

    event_class = cfg["EVENT_CLASS"]
    if isinstance(event_class, str):
        event_class = import_string(event_class)

    validator = cfg["VALIDATOR"]
    if isinstance(validator, str):
        validator = import_string(validator)

    return AuthEventsConfig(
        cache_key_prefix=cfg["CACHE_KEY_PREFIX"],
        stream=cfg["STREAM"],
        group=cfg["GROUP"],
        subject_claim=cfg["SUBJECT_CLAIM"],
        event_class=event_class,
        validator=validator,
        cache_ttl=cfg.get("CACHE_TTL", 86400),
    )
