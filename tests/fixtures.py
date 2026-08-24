from dataclasses import dataclass

from django_auth_external import TokenConfig
from django_auth_external.exceptions import AuthExternalError
from django_auth_external.token import validate_token

from django_auth_events.events import SessionInvalidatedEvent
from django_auth_events.exceptions import TokenValidationError


@dataclass
class ConcreteSessionInvalidatedEvent(SessionInvalidatedEvent):
    user_id: str

    @property
    def identifier(self) -> str:
        return self.user_id


TOKEN_CONFIG = TokenConfig(
    secret_key="test-secret-key-at-least-32-bytes-long!!",
    claims=["user_id", "email"],
    subject_claim="user_id",
    token_ttl_seconds=3600,
)


def token_validator(token: str) -> dict:
    try:
        return validate_token(token, TOKEN_CONFIG)
    except AuthExternalError as exc:
        raise TokenValidationError(str(exc)) from exc
