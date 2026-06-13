#!/usr/bin/env python3
"""Tests for newspaper URL resolver."""

import sys
sys.path.insert(0, "backend")

from newspaper_resolver import resolve_newspaper_url, NewspaperNotFoundError, InvalidDateError, InvalidPageError


def test_lokmat_nagpur():
    result = resolve_newspaper_url("Lokmat Nagpur", "2026-06-12", 2)
    expected = "https://epaper.lokmat.com/main-editions/Nagpur%20Main/2026-06-12/2"
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ Lokmat Nagpur test passed")


def test_lokmat_hello_nagpur():
    result = resolve_newspaper_url("Lokmat Hello Nagpur", "2026-06-12", 2)
    expected = "https://epaper.lokmat.com/sub-editions/Hello%20Nagpur/2026-06-12/2"
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ Lokmat Hello Nagpur test passed")


def test_lokmat_hello_wardha():
    result = resolve_newspaper_url("Lokmat Hello Wardha", "2026-06-12", 2)
    expected = "https://epaper.lokmat.com/sub-editions/Hello%20Wardha/2026-06-12/2"
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ Lokmat Hello Wardha test passed")


def test_lokmat_apna_samachar():
    result = resolve_newspaper_url("Lokmat Apna Samachar", "2026-06-12", 2)
    expected = "https://epaper.lokmat.com/lokmatsamachar/sub-editions/Apna%20Samachar/2026-06-12/2"
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ Lokmat Apna Samachar test passed")


def test_lokmat_samachar_apna_nagpur():
    result = resolve_newspaper_url("Lokmat Samachar Apna Nagpur", "2026-06-12", 2)
    expected = "https://epaper.lokmat.com/lokmatsamachar/sub-editions/Apna%20Nagpur/2026-06-12/2"
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ Lokmat Samachar Apna Nagpur test passed")


def test_lokmat_samachar_apna_vidarbha():
    result = resolve_newspaper_url("Lokmat Samachar Apna Vidarbha", "2026-06-12", 2)
    expected = "https://epaper.lokmat.com/lokmatsamachar/sub-editions/Apna%20Vidarbha/2026-06-12/2"
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ Lokmat Samachar Apna Vidarbha test passed")


def test_the_hitavada():
    result = resolve_newspaper_url("The Hitavada", "2026-06-12", 2)
    expected = "https://www.ehitavada.com/index.php?edition=Mpage&date=2026-06-12&page=2"
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ The Hitavada test passed")


def test_the_hitavada_city_line():
    result = resolve_newspaper_url("The Hitavada City Line", "2026-06-12", 2)
    expected = "https://www.ehitavada.com/index.php?edition=NCpage&date=2026-06-12&page=2"
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ The Hitavada City Line test passed")


def test_the_hitavada_vidarbha_line():
    result = resolve_newspaper_url("The Hitavada Vidarbha Line", "2026-06-12", 2)
    expected = "https://www.ehitavada.com/index.php?edition=VLpage&date=2026-06-12&page=2"
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ The Hitavada Vidarbha Line test passed")


def test_invalid_newspaper():
    try:
        resolve_newspaper_url("Invalid Newspaper", "2026-06-12", 2)
        assert False, "Should have raised NewspaperNotFoundError"
    except NewspaperNotFoundError:
        print("✓ Invalid newspaper test passed")


def test_invalid_date():
    try:
        resolve_newspaper_url("Lokmat Nagpur", "2026-13-01", 2)
        assert False, "Should have raised InvalidDateError"
    except InvalidDateError:
        print("✓ Invalid date test passed")


def test_invalid_page():
    try:
        resolve_newspaper_url("Lokmat Nagpur", "2026-06-12", 0)
        assert False, "Should have raised InvalidPageError"
    except InvalidPageError:
        print("✓ Invalid page test passed")


def test_page_one():
    result = resolve_newspaper_url("Lokmat Nagpur", "2026-06-12", 1)
    expected = "https://epaper.lokmat.com/main-editions/Nagpur%20Main/2026-06-12/1"
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ Page 1 test passed")


def test_date_validation():
    try:
        resolve_newspaper_url("Lokmat Nagpur", "invalid-date", 1)
        assert False, "Should have raised InvalidDateError"
    except InvalidDateError:
        print("✓ Date validation test passed")


if __name__ == "__main__":
    print("Running newspaper resolver tests...")

    test_lokmat_nagpur()
    test_lokmat_hello_nagpur()
    test_lokmat_hello_wardha()
    test_lokmat_apna_samachar()
    test_lokmat_samachar_apna_nagpur()
    test_lokmat_samachar_apna_vidarbha()
    test_the_hitavada()
    test_the_hitavada_city_line()
    test_the_hitavada_vidarbha_line()

    test_invalid_newspaper()
    test_invalid_date()
    test_invalid_page()
    test_page_one()
    test_date_validation()

    print("\n✅ All tests passed!")
