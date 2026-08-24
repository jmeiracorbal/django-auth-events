from datetime import datetime, timezone

from .config import _build_config
from .exceptions import TokenValidationError
from .store import is_invalidated


class AuthEventsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.config = _build_config()

    def __call__(self, request):
        request.auth_payload = None
        token = self._extract_token(request)
        if token:
            try:
                payload = self.config.validator(token)
                identifier = payload.get(self.config.subject_claim)
                token_iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
                if identifier is None or not is_invalidated(identifier, token_iat, self.config):
                    request.auth_payload = payload
            except TokenValidationError:
                pass
        return self.get_response(request)

    def _extract_token(self, request) -> str | None:
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if header.startswith("Bearer "):
            return header[7:]
        return None
