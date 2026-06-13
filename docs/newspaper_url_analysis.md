# Newspaper URL Analysis Report

## Overview
This document provides detailed analysis of the 9 verified newspaper URLs provided by the user. Each newspaper has been analyzed to extract URL structure components and determine patterns for URL generation and substitution.

## URL Analysis Summary

### 1. Lokmat Nagpur
**Sample URL:** https://epaper.lokmat.com/main-editions/Nagpur%20Main/2026-06-13/1

**Date Extraction Analysis:**
- Location: Path segment after base URL
- Format: YYYY-MM-DD (2026-06-13)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Supports YYYY-MM-DD format

**Page Extraction Analysis:**
- Location: Final path segment
- Format: Integer (1)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Supports any positive integer

**Edition Extraction Analysis:**
- Location: Path segment in base URL
- Format: URL-encoded string (Nagpur%20Main)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Requires URL encoding of spaces

**URL Structure Explanation:**
The URL uses a static path structure with edition as part of the base URL, followed by date and page as sequential path segments. The edition is URL-encoded to handle spaces. This structure supports direct URL construction without discovery.

### 2. Lokmat Hello Nagpur
**Sample URL:** https://epaper.lokmat.com/sub-editions/Hello%20Nagpur/2026-06-13/1

**Date Extraction Analysis:**
- Location: Path segment after base URL
- Format: YYYY-MM-DD (2026-06-13)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Supports YYYY-MM-DD format

**Page Extraction Analysis:**
- Location: Final path segment
- Format: Integer (1)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Supports any positive integer

**Edition Extraction Analysis:**
- Location: Path segment in base URL
- Format: URL-encoded string (Hello%20Nagpur)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Requires URL encoding of spaces

**URL Structure Explanation:**
Identical structure to Lokmat Nagpur but uses sub-editions path instead of main-editions. Maintains the same path-based pattern with date and page as sequential segments.

### 3. Lokmat Hello Wardha
**Sample URL:** https://epaper.lokmat.com/sub-editions/Hello%20Wardha/2026-06-13/1

**Date Extraction Analysis:**
- Location: Path segment after base URL
- Format: YYYY-MM-DD (2026-06-13)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Supports YYYY-MM-DD format

**Page Extraction Analysis:**
- Location: Final path segment
- Format: Integer (1)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Supports any positive integer

**Edition Extraction Analysis:**
- Location: Path segment in base URL
- Format: URL-encoded string (Hello%20Wardha)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Requires URL encoding of spaces

**URL Structure Explanation:**
Follows the same pattern as other Lokmat sub-editions, using sub-editions path with URL-encoded edition names and sequential date/page path segments.

### 4. Lokmat Apna Samachar
**Sample URL:** https://epaper.lokmat.com/lokmatsamachar/sub-editions/Apna%20Samachar/2026-06-14/1

**Date Extraction Analysis:**
- Location: Path segment after base URL
- Format: YYYY-MM-DD (2026-06-14)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Supports YYYY-MM-DD format

**Page Extraction Analysis:**
- Location: Final path segment
- Format: Integer (1)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Supports any positive integer

**Edition Extraction Analysis:**
- Location: Path segment in base URL
- Format: URL-encoded string (Apna%20Samachar)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Requires URL encoding of spaces

**URL Structure Explanation:**
Uses lokmatsamachar domain with sub-editions path, maintaining the consistent path-based structure across all Lokmat newspapers. The base URL includes the domain and sub-editions path.

### 5. Lokmat Samachar Apna Nagpur
**Sample URL:** https://epaper.lokmat.com/lokmatsamachar/sub-editions/Apna%20Nagur/2026-06-13/1

**Date Extraction Analysis:**
- Location: Path segment after base URL
- Format: YYYY-MM-DD (2026-06-13)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Supports YYYY-MM-DD format

**Page Extraction Analysis:**
- Location: Final path segment
- Format: Integer (1)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Supports any positive integer

**Edition Extraction Analysis:**
- Location: Path segment in base URL
- Format: URL-encoded string (Apna%20Nagur)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Requires URL encoding of spaces

**URL Structure Explanation:**
Note: The edition name appears to be "Apna Nagur" which may be a typo in the sample URL. The structure follows the same pattern as other Lokmat Samachar newspapers with the lokmatsamachar domain.

### 6. Lokmat Samachar Apna Vidarbha
**Sample URL:** https://epaper.lokmat.com/lokmatsamachar/sub-editions/Apna%20Vidarbha/2026-06-13/1

**Date Extraction Analysis:**
- Location: Path segment after base URL
- Format: YYYY-MM-DD (2026-06-13)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Supports YYYY-MM-DD format

**Page Extraction Analysis:**
- Location: Final path segment
- Format: Integer (1)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Supports any positive integer

**Edition Extraction Analysis:**
- Location: Path segment in base URL
- Format: URL-encoded string (Apna%20Vidarbha)
- Extraction Pattern: `{base_url}{edition}/{date}/{page}`
- Substitution: Requires URL encoding of spaces

**URL Structure Explanation:**
Follows the established pattern for Lokmat Samachar newspapers, using the lokmatsamachar domain with sub-editions path structure.

### 7. The Hitavada
**Sample URL:** https://www.ehitavada.com/index.php?edition=Mpage&date=2026-06-14&page=1

**Date Extraction Analysis:**
- Location: Query parameter
- Format: YYYY-MM-DD (2026-06-14)
- Extraction Pattern: `{base_url}?edition={edition}&date={date}&page={page}`
- Substitution: Supports YYYY-MM-DD format

**Page Extraction Analysis:**
- Location: Query parameter
- Format: Integer (1)
- Extraction Pattern: `{base_url}?edition={edition}&date={date}&page={page}`
- Substitution: Supports any positive integer

**Edition Extraction Analysis:**
- Location: Query parameter
- Format: String (Mpage)
- Extraction Pattern: `{base_url}?edition={edition}&date={date}&page={page}`
- Substitution: Supports any string (no URL encoding needed)

**URL Structure Explanation:**
Uses a query parameter structure with edition, date, and page as separate query parameters. The base URL is the main domain with index.php, and all parameters are passed via the query string.

### 8. The Hitavada City Line
**Sample URL:** https://www.ehitavada.com/index.php?edition=NCpage&date=2026-06-14&page=1

**Date Extraction Analysis:**
- Location: Query parameter
- Format: YYYY-MM-DD (2026-06-14)
- Extraction Pattern: `{base_url}?edition={edition}&date={date}&page={page}`
- Substitution: Supports YYYY-MM-DD format

**Page Extraction Analysis:**
- Location: Query parameter
- Format: Integer (1)
- Extraction Pattern: `{base_url}?edition={edition}&date={date}&page={page}`
- Substitution: Supports any positive integer

**Edition Extraction Analysis:**
- Location: Query parameter
- Format: String (NCpage)
- Extraction Pattern: `{base_url}?edition={edition}&date={date}&page={page}`
- Substitution: Supports any string

**URL Structure Explanation:**
Identical structure to The Hitavada but with different edition parameter (NCpage vs Mpage). Maintains the query-based URL structure for all The Hitavada newspapers.

### 9. The Hitavada Vidarbha Line
**Sample URL:** https://www.ehitavada.com/index.php?edition=VLpage&date=2026-06-14&page=1

**Date Extraction Analysis:**
- Location: Query parameter
- Format: YYYY-MM-DD (2026-06-14)
- Extraction Pattern: `{base_url}?edition={edition}&date={date}&page={page}`
- Substitution: Supports YYYY-MM-DD format

**Page Extraction Analysis:**
- Location: Query parameter
- Format: Integer (1)
- Extraction Pattern: `{base_url}?edition={edition}&date={date}&page={page}`
- Substitution: Supports any positive integer

**Edition Extraction Analysis:**
- Location: Query parameter
- Format: String (VLpage)
- Extraction Pattern: `{base_url}?edition={edition}&date={date}&page={page}`
- Substitution: Supports any string

**URL Structure Explanation:**
Consistent with the Hitavada URL structure pattern, with VLpage as the edition identifier. All The Hitavada newspapers follow the same query parameter structure.

## URL Type Classification

### Path-Based URLs (6 newspapers):
1. Lokmat Nagpur
2. Lokmat Hello Nagpur
3. Lokmat Hello Wardha
4. Lokmat Apna Samachar
5. Lokmat Samachar Apna Nagpur
6. Lokmat Samachar Apna Vidarbha

**Characteristics:**
- Edition as part of base URL path
- Date and page as sequential path segments
- No query string parameters
- Supports direct URL construction
- No discovery required

### Query-Based URLs (3 newspapers):
1. The Hitavada
2. The Hitavada City Line
3. The Hitavada Vidarbha Line

**Characteristics:**
- Edition, date, and page as query parameters
- Base URL is simple domain with index.php
- All parameters passed via query string
- Supports direct URL construction
- No discovery required

## Substitution Support Analysis

### Date Substitution:
**All 9 newspapers:** Support YYYY-MM-DD format
- Path-based: Date as path segment
- Query-based: Date as query parameter

### Page Substitution:
**All 9 newspapers:** Support integer values
- Path-based: Page as final path segment
- Query-based: Page as query parameter

### Edition Substitution:
**All 9 newspapers:** Support edition substitution
- Path-based: URL-encoded edition in path
- Query-based: Plain string edition parameter

## Implementation Implications

### Path-Based Newspapers:
- **Complexity:** Low - simple path construction
- **Encoding:** Requires URL encoding for spaces
- **Discovery:** Not required
- **Error Handling:** Path-related errors

### Query-Based Newspapers:
- **Complexity:** Medium - query parameter construction
- **Encoding:** Simple string parameters
- **Discovery:** Not required
- **Error Handling:** Parameter validation

## URL Structure Summary Table

| Newspaper | URL Type | Date Location | Page Location | Edition Location | Complexity |
|-----------|----------|---------------|---------------|------------------|------------|
| Lokmat Nagpur | Path | Path | Path | Path | Low |
| Lokmat Hello Nagpur | Path | Path | Path | Path | Low |
| Lokmat Hello Wardha | Path | Path | Path | Path | Low |
| Lokmat Apna Samachar | Path | Path | Path | Path | Low |
| Lokmat Samachar Apna Nagpur | Path | Path | Path | Path | Medium |
| Lokmat Samachar Apna Vidarbha | Path | Path | Path | Path | Low |
| The Hitavada | Query | Query | Query | Query | Medium |
| The Hitavada City Line | Query | Query | Query | Query | Medium |
| The Hitvar Vidarbha Line | Query | Query | Query | Query | Medium |

## Conclusion

The user-provided URLs reveal a clear distinction between two URL structure types:

1. **Path-Based Structure (6 newspapers):** Consistent pattern with edition in base URL, date and page as sequential path segments
2. **Query-Based Structure (3 newspapers):** Consistent pattern with all parameters as query parameters

Both types support substitution for all components (edition, date, page) with standardized formats. The implementation can be approached with confidence in the URL patterns, though attention must be paid to URL encoding requirements for path-based newspapers.

The analysis provides a solid foundation for implementing newspaper URL resolution functionality with minimal risk.
