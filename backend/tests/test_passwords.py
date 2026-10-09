import pytest
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.passwords import password_meets_policy


def test_hash_uses_argon2id_with_the_required_parameters(passwords):
    assert passwords.hash("a-long-enough-password").startswith("$argon2id$v=19$m=19456,t=2,p=1$")


def test_each_hash_has_its_own_salt(passwords):
    assert passwords.hash("a-long-enough-password") != passwords.hash("a-long-enough-password")


def test_verify_and_update_accepts_the_right_password(passwords):
    stored = passwords.hash("a-long-enough-password")

    assert passwords.verify_and_update("a-long-enough-password", stored) == (True, None)


def test_verify_and_update_rejects_the_wrong_password(passwords):
    stored = passwords.hash("a-long-enough-password")

    verified, updated = passwords.verify_and_update("another-long-password", stored)

    assert verified is False
    assert updated is None


def test_verify_and_update_rejects_a_missing_hash(passwords):
    assert passwords.verify_and_update("a-long-enough-password", None) == (False, None)


def test_verify_and_update_rehashes_outdated_parameters(passwords):
    outdated = PasswordHash(
        (Argon2Hasher(time_cost=1, memory_cost=8192, parallelism=1),)
    ).hash("a-long-enough-password")

    verified, updated = passwords.verify_and_update("a-long-enough-password", outdated)

    assert verified is True
    assert updated.startswith("$argon2id$v=19$m=19456,t=2,p=1$")


@pytest.mark.parametrize(
    "password",
    ["ten-charac", "a" * 128, "a-long-enough-password"],
)
def test_password_meets_policy(password):
    assert password_meets_policy(password, "ayesha@example.com") is True


@pytest.mark.parametrize(
    ("password", "email"),
    [
        ("too-short", "ayesha@example.com"),
        ("a" * 129, "ayesha@example.com"),
        ("my-ayesha-password", "Ayesha@example.com"),
        ("AYESHA-is-my-password", "ayesha@example.com"),
    ],
)
def test_password_fails_policy(password, email):
    assert password_meets_policy(password, email) is False
