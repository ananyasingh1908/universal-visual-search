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
expected = "https://epaper.lokmat.com/lokmatsamachar/sub-editions/Apna%20Nagur/2026-06-12/2"
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

print("\n✅ All tests passed!")
