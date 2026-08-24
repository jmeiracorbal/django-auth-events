from tests.fixtures import ConcreteSessionInvalidatedEvent


def test_session_invalidated_event_from_dict():
    data = {
        "event_type": "session.invalidated",
        "user_id": "abc-123",
        "occurred_at": "2026-01-01T00:00:00+00:00",
    }
    event = ConcreteSessionInvalidatedEvent.from_dict(data)
    assert event.identifier == "abc-123"
    assert event.event_type == "session.invalidated"


def test_session_invalidated_event_to_dict():
    event = ConcreteSessionInvalidatedEvent(event_type="session.invalidated", user_id="abc-123")
    d = event.to_dict()
    assert d["user_id"] == "abc-123"
    assert d["event_type"] == "session.invalidated"


def test_identifier_delegates_to_user_id():
    event = ConcreteSessionInvalidatedEvent(event_type="session.invalidated", user_id="xyz")
    assert event.identifier == "xyz"
