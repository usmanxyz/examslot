import threading

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128

DUMMY_PASSWORD = "examslot-dummy-verification-password"


def password_meets_policy(password: str, email: str) -> bool:
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        return False
    local_part = email.split("@", 1)[0].strip().lower()
    return local_part not in password.lower()


class PasswordService:
    def __init__(self, concurrency: int) -> None:
        self._hasher = PasswordHash((Argon2Hasher(time_cost=2, memory_cost=19456, parallelism=1),))
        self._gate = threading.BoundedSemaphore(concurrency)
        self._dummy_hash = self._hasher.hash(DUMMY_PASSWORD)

    def hash(self, password: str) -> str:
        with self._gate:
            return self._hasher.hash(password)

    def verify_and_update(self, password: str, password_hash: str | None) -> tuple[bool, str | None]:
        with self._gate:
            if password_hash is None:
                self._hasher.verify(password, self._dummy_hash)
                return False, None
            return self._hasher.verify_and_update(password, password_hash)
