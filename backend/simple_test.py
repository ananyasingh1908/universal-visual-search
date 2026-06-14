#!/usr/bin/env python3
"""Simple tests for newspaper URL resolver."""

import sys
sys.path.insert(0, "backend")

from newspaper_resolver import resolve_newspaper_url, NewspaperNotFoundError, InvalidDateError, InvalidPageError

# Test basic functionality
print("Testing newspaper resolver...")

# Test Lokmat group
result = resolve_newspaper_url("Lokmat Nagpur", "2026-06-12", 2)
expected = "https://epaper.lokmat.com/main-editions/Nagpur%20Main/2026-06-12/2"
print(f"Lokmat Nagpur: {result}")
assert result == expected, f"Expected {expected}, got {result}"

result = resolve_newspaper_url("Lokmat Hello Nagpur", "2026-06-12", 2)
expected = "https://epaper.lokmat.com/sub-editions/Hello%20Nagpur/2026-06-12/2"
print(f"Lokmat Hello Nagpur: {result}")
assert result == expected, f"Expected {expected}, got {result}"

result = resolve_newspaper_url("Lokmat Hello Wardha", "2026-06-12", 2)
expected = "https://epaper.lokmat.com/sub-editions/Hello%20Wardha/2026-06-12/2"
print(f"Lokmat Hello Wardha: {result}")
assert result == expected, f"Expected {expected}, got {result}"

result = resolve_newspaper_url("Lokmat Apna Samachar", "2026-06-12", 2)
expected = "https://epaper.lokmat.com/lokmatsamachar/sub-editions/Apna%20Samachar/2026-06-12/2"
print(f"Lokmat Apna Samachar: {result}")
assert result == expected, f"Expected {expected}, got {result}"

result = resolve_newspaper_url("Lokmat Samachar Apna Nagpur", "2026-06-12", 2)
expected = "https://epaper.lokmat.com/lokmatsamachar/sub-editions/Apna%20Nagpur/2026-06-12/2"
print(f"Lokmat Samachar Apna Nagpur: {result}")
assert result == expected, f"Expected {expected}, got {result}"

result = resolve_newspaper_url("Lokmat Samachar Apna Vidarbha", "2026-06-12", 2)
expected = "https://epaper.lokmat.com/lokmatsamachar/sub-editions/Apna%20Vidarbha/2026-06-12/2"
print(f"Lokmat Samachar Apna Vidarbha: {result}")
assert result == expected, f"Expected {expected}, got {result}"

# Test The Hitavada group
result = resolve_newspaper_url("The Hitavada", "2026-06-12", 2)
expected = "https://www.ehitavada.com/index.php?edition=Mpage&date=2026-06-12&page=2"
print(f"The Hitavada: {result}")
assert result == expected, f"Expected {expected}, got {result}"

result = resolve_newspaper_url("The Hitavada City Line", "2026-06-12", 2)
expected = "https://www.ehitavada.com/index.php?edition=NCpage&date=2026-06-12&page=2"
print(f"The Hitavada City Line: {result}")
assert result == expected, f"Expected {expected}, got {result}"

result = resolve_newspaper_url("The Hitavada Vidarbha Line", "2026-06-12", 2)
expected = "https://www.ehitavada.com/index.php?edition=VLpage&date=2026-06-12&page=2"
print(f"The Hitavada Vidarbha Line: {result}")
assert result == expected, f"Expected {expected}, got {result}"

# Test NEW new newspapers
result = resolve_newspaper_url("Navarashtra", "2026-06-13", 1)
expected = "https://epaper.navarashtra.com/nagpur/nagpur/2026-06-13/1"
print(f"Navarashtra: {result}")
assert result == expected, f"Expected {expected}, got {result}"

result = resolve_newspaper_url("Navbharat Nagpur", "2026-06-13", 1)
expected = "https://epaper.navbharatlive.com/nagpur/nagpur/2026-06-13/1"
print(f"Navbharat Nagpur: {result}")
assert result == expected, f"Expected {expected}, got {result}"

result = resolve_newspaper_url("Navbharat Nagpur Plus", "2026-06-11", 1)
expected = "https://epaper.navbharatlive.com/nagpur/nagpurplus/2026-06-11/1"
print(f"Navbharat Nagpur Plus: {result}")
assert result == expected, f"Expected {expected}, got {result}"

result = resolve_newspaper_url("Lokvahini", "2026-06-13", 1)
expected = "https://epaper.lokvahini.com/index.php?edition=Mpage&date=2026-06-13&page=1"
print(f"Lokvahini: {result}")
assert result == expected, f"Expected {expected}, got {result}"

result = resolve_newspaper_url("Lokshahi Varta Edition 16", "13/06/2026", 1)
expected = "https://lokshahivarta.co.in/?url=home&ced=16&date=13/06/2026&page=1"
print(f"Lokshahi Varta Edition 16: {result}")
assert result == expected, f"Expected {expected}, got {result}"

result = resolve_newspaper_url("Lokshahi Varta Edition 11", "13/06/2026", 1)
expected = "https://lokshahivarta.co.in/?url=home&ced=11&date=13/06/2026&page=1"
print(f"Lokshahi Varta Edition 11: {result}")
assert result == expected, f"Expected {expected}, got {result}"

result = resolve_newspaper_url("Deshonnati Nagpur", "20260613", 1)
expected = "https://epaper.deshonnati.com/edition/Nagpur/DESHONATI_NAGP/DESHONATI_NAGP_20260613/page/1"
print(f"Deshonnati Nagpur: {result}")
assert result == expected, f"Expected {expected}, got {result}"

print("\nAll tests passed!")
