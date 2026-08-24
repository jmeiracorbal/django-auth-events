import logging

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from streambus import EventListener, RedisConfig, RedisStreamsTransport

from django_auth_events.config import _build_config
from django_auth_events.events import SessionInvalidatedEvent
from django_auth_events.store import invalidate_user

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Consume auth session invalidation events and update the cache"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = _build_config()

    def handle(self, *args, **options):
        redis_url = getattr(django_settings, "REDIS_URL", None)
        if not redis_url:
            raise ImproperlyConfigured("REDIS_URL is required but not configured")
        transport = RedisStreamsTransport(RedisConfig(url=redis_url))
        listener = EventListener(
            stream=self._config.stream,
            group=self._config.group,
            handler=self._on_event,
            event_class=self._config.event_class,
            transport=transport,
        )
        self.stdout.write(f"Listening on {self._config.stream} (group: {self._config.group})")
        listener.run()

    def _on_event(self, event: SessionInvalidatedEvent) -> None:
        invalidate_user(event.identifier, self._config)
        logger.info("Session invalidated for identifier %s", event.identifier)
