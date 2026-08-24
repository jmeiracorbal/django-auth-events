from dataclasses import dataclass

from streambus import StreamBusEvent


@dataclass
class SessionInvalidatedEvent(StreamBusEvent):
    """Base contract for session invalidation events.

    Subclasses must implement the identifier property, mapping whichever field
    the application uses to identify users to a single stable string key.
    """

    @property
    def identifier(self) -> str:
        raise NotImplementedError
