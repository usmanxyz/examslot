import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import Settings

ALGORITHM = "HS256"
LEEWAY_SECONDS = 10
REQUIRED_CLAIMS = ["sub", "ver", "iat", "exp", "iss", "aud"]


class TokenService:
    def __init__(self, settings: Settings) -> None:
        self._secret = settings.JWT_SECRET
        self._issuer = settings.JWT_ISSUER
        self._audiences = {
            "student": settings.JWT_STUDENT_AUDIENCE,
            "admin": settings.JWT_ADMIN_AUDIENCE,
        }
        self._minutes = {
            "student": settings.STUDENT_TOKEN_MINUTES,
            "admin": settings.ADMIN_TOKEN_MINUTES,
        }

    def lifetime_seconds(self, area: str) -> int:
        return self._minutes[area] * 60

    def issue(self, area: str, subject: uuid.UUID, token_version: int) -> str:
        issued = datetime.now(UTC)
        return jwt.encode(
            {
                "sub": str(subject),
                "ver": token_version,
                "iat": issued,
                "exp": issued + timedelta(minutes=self._minutes[area]),
                "iss": self._issuer,
                "aud": self._audiences[area],
            },
            self._secret,
            algorithm=ALGORITHM,
        )

    def decode(self, area: str, token: str) -> tuple[uuid.UUID, int]:
        claims = jwt.decode(
            token,
            self._secret,
            algorithms=[ALGORITHM],
            audience=self._audiences[area],
            issuer=self._issuer,
            leeway=LEEWAY_SECONDS,
            options={"require": REQUIRED_CLAIMS},
        )
        return uuid.UUID(claims["sub"]), int(claims["ver"])
