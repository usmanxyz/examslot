import pytest

from app.utils.normalize import (
    normalize_cnic,
    normalize_code,
    normalize_email,
    normalize_mobile,
    normalize_name,
    normalize_phone,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("  Ayesha@Example.COM ", "ayesha@example.com"), ("a@b.com", "a@b.com")],
)
def test_normalize_email(raw, expected):
    assert normalize_email(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Ayesha   Siddiqui ", "Ayesha Siddiqui"),
        ("House 1,\tStreet 5", "House 1, Street 5"),
        ("Lahore", "Lahore"),
    ],
)
def test_normalize_name(raw, expected):
    assert normalize_name(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), [(" cs-2101 ", "CS-2101"), ("lhr", "LHR")])
def test_normalize_code(raw, expected):
    assert normalize_code(raw) == expected


def test_normalize_code_rejects_inner_spaces():
    with pytest.raises(ValueError):
        normalize_code("CS 2101")


@pytest.mark.parametrize(
    "raw", ["35202-1234567-1", "3520212345671", " 35202 1234567 1 ", "35202.1234567.1"]
)
def test_normalize_cnic(raw):
    assert normalize_cnic(raw) == "3520212345671"


@pytest.mark.parametrize("raw", ["35202-12345-1", "", "abcdefghijklm", "352021234567"])
def test_normalize_cnic_rejects_other_lengths(raw):
    with pytest.raises(ValueError):
        normalize_cnic(raw)


@pytest.mark.parametrize(
    "raw", ["0300 1234567", "03001234567", "+92 300 1234567", "923001234567", "0092 300 1234567"]
)
def test_normalize_mobile(raw):
    assert normalize_mobile(raw) == "+923001234567"


@pytest.mark.parametrize("raw", ["042 35761234", "0300 123456", "+924235761234"])
def test_normalize_mobile_rejects_other_numbers(raw):
    with pytest.raises(ValueError):
        normalize_mobile(raw)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("042 35761234", "+924235761234"),
        ("0300 1234567", "+923001234567"),
        ("+92 42 35761234", "+924235761234"),
    ],
)
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("raw", ["042 3576", "0", ""])
def test_normalize_phone_rejects_short_numbers(raw):
    with pytest.raises(ValueError):
        normalize_phone(raw)
