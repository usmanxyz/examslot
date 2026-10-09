import re

_WHITESPACE = re.compile(r"\s+")
_PUNCTUATION = re.compile(r"[\s()\-.]")
_CNIC = re.compile(r"[0-9]{13}")
_MOBILE = re.compile(r"3[0-9]{9}")
_PHONE = re.compile(r"[1-9][0-9]{8,9}")

CNIC_MESSAGE = "Enter 13 digits, for example 00000-0000000-1."
MOBILE_MESSAGE = "Enter a Pakistani mobile number, for example 0300 1234567."
PHONE_MESSAGE = "Enter a Pakistani phone number, for example 042 35761234."
CODE_MESSAGE = "A code cannot contain spaces."


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_name(value: str) -> str:
    return _WHITESPACE.sub(" ", value.strip())


def normalize_code(value: str) -> str:
    code = value.strip().upper()
    if _WHITESPACE.search(code):
        raise ValueError(CODE_MESSAGE)
    return code


def normalize_cnic(value: str) -> str:
    digits = _PUNCTUATION.sub("", value.strip())
    if not _CNIC.fullmatch(digits):
        raise ValueError(CNIC_MESSAGE)
    return digits


def normalize_mobile(value: str) -> str:
    national = _to_national(value)
    if not _MOBILE.fullmatch(national):
        raise ValueError(MOBILE_MESSAGE)
    return f"+92{national}"


def normalize_phone(value: str) -> str:
    national = _to_national(value)
    if not _PHONE.fullmatch(national):
        raise ValueError(PHONE_MESSAGE)
    return f"+92{national}"


def _to_national(value: str) -> str:
    digits = _PUNCTUATION.sub("", value.strip())
    if digits.startswith("+92"):
        return digits[3:]
    if digits.startswith("0092"):
        return digits[4:]
    if digits.startswith("92") and len(digits) in {11, 12}:
        return digits[2:]
    if digits.startswith("0"):
        return digits[1:]
    return digits
