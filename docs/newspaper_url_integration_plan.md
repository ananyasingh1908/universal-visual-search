# Newspaper URL Integration Plan - Audit Document

## 1. Current Architecture

### Frontend Architecture
- **Framework**: Next.js 16.2.7 with React 19.2.4
- **Architecture**: Client-side application with React state management
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios for API communication

### Backend Architecture
- **Framework**: FastAPI 0.136.3 with Python 3.12+
- **Architecture**: RESTful API with asynchronous processing
- **Database**: File-based storage (JSON files in `/data/` directory)
- **OCR Engine**: Google Vision API (primary) + EasyOCR (fallback)
- **Web Scraping**: Playwright for browser automation

## 2. Existing Workflow

### Frontend User Flow:
1. Upload Image or enter URL to scan
2. OCR processing extracts text from images
3. Website scanning detects pages and extracts text
4. User can search for keywords in OCR results
5. User can highlight matches in images
6. User can select newspapers and regions from menus
7. Selected newspaper filters region availability

### Backend Processing Flow:
1. Receive OCR/image upload request
2. Process with Google Vision or EasyOCR
3. Save OCR results to JSON in `/data/` directory
4. For website scans: create jobs with polling mechanism
5. Generate screenshots saved to `/screenshots/` directory
6. Provide endpoints for searching, highlighting, and downloading results

## 3. Files Involved

### Core Backend Files:
- `backend/main.py` (549 lines) - All API endpoints
- `backend/ocr_service.py` (732 lines) - OCR processing logic
- `backend/highlight_service.py` (197 lines) - Image highlighting
- `backend/news_keywords.py` (385 lines) - Keyword catalog
- `backend/lokmat_scraper.py` (558 lines) - Newspaper scraper

### Core Frontend Files:
- `frontend/app/page.tsx` (34118 lines) - Main UI component
- `frontend/app/layout.tsx` (752 lines) - Layout wrapper
- `frontend/lib/utils.ts` (3 lines) - Helper utilities

### Configuration Files:
- `backend/.env` (1 line) - Environment variables
- `frontend/package.json` - Dependencies and scripts
- `backend/requirements.txt` - Python dependencies

## 4. Functions Involved

### Backend Functions:
- `process_image_document()` - OCR image processing
- `run_ocr()` - Core OCR extraction
- `scan_website()` - Website scanning initiation
- `_run_scan_job()` - Asynchronous website scanning
- `scrape_lokmat_times_edition()` - Newspaper scraping
- `highlight_keywords()` - Image highlighting

### Frontend Functions:
- `uploadImage()` - Handle image upload and OCR
- `scanWebsite()` - Initiate website scan
- `searchNews()` - Search OCR results
- `highlightNews()` - Highlight matches
- `handleNewspaperClick()` - Newspaper selection
- `switchPage()` - Page navigation

## 5. Where Newspaper Selection Currently Enters the Workflow

Newspaper selection is integrated into the main UI but doesn't actively drive any scanning workflow:

### Current Implementation:
- Located in Newspaper Menu component (lines 942-1080)
- Selection updates `selectedNewspaper` state
- Filters available regions in `getRegionAvailable()` function
- Available regions displayed but never used in scanning workflow

### Integration Points:
- **News Search**: Uses locked keyword set, not newspaper-specific
- **Website Scanning**: No newspaper-specific parameters
- **Newspaper Scraping**: Uses `scrape-lokmat-times` endpoint with `edition_name` and `date` parameters, unrelated to UI newspaper selection

### Missing Integration:
- No newspaper-specific OCR configuration
- No newspaper-specific keyword filters
- No newspaper-specific region-based processing

## 6. Where Region Selection Currently Enters the Workflow

Region selection is display-only and has no active workflow integration:

### Current Implementation:
- Region dropdown and grid buttons (lines 997-1074)
- Region availability shown via `getRegionAvailable()`
- Selected region stored in `selectedRegion` state
- Display shows availability for selected newspaper

### Missing Integration:
- No region-specific scanning parameters
- No region-based keyword filtering
- No region-specific newspaper selection
- Region selection doesn't trigger any backend processing

## 7. Best Location to Add a DATE Selector

### Recommended Location: Backend Scan Endpoint Configuration

**Optimal Place**: In the `/scan-website` endpoint (`backend/main.py:266-286`)

**Rationale**:
1. Website scanning already requires URL resolution
2. Date selector can be added as optional parameter alongside URL
3. Maintains consistency with existing `LokmatScrapeRequest` pattern (edition_name, date)
4. Enables date-based pagination and version control for newspaper websites
5. Backend can validate and format date consistently

**Implementation Option**:
```python
class EnhancedScanRequest(BaseModel):
    url: str
    date: Optional[str] = None  # YYYY-MM-DD format
```

## 8. Best Location to Add URL Resolution

### Recommended Location: `/scan-website` Endpoint Processing (`backend/main.py:308-420`)

**Rationale**:
1. Website scanning is the primary URL-based feature
2. All URL processing logic already exists in `_run_scan_job()`
3. Page navigation uses `_build_page_url()` helper (lines 247-263)
4. Date-based resolution needs URL manipulation capabilities
5. Centralized in one location for maintainability

**Existing URL Resolution Components**:
- `_build_page_url()` - Builds paginated URLs
- `_detect_total_pages()` - Detects total pages on website
- Page navigation logic in `_run_scan_job()` loop

## 9. Files That Will Need Modification

### Essential Files for Date/URL Feature:
1. **`backend/main.py`** - Modify `/scan-website` endpoint to accept date parameter
2. **`backend/main.py`** - Update `_run_scan_job()` to use date for URL resolution
3. **`backend/main.py`** - Update `_build_page_url()` for date-based URL patterns

### Supporting Files:
4. **`frontend/app/page.tsx`** - Add date selector UI component
5. **`frontend/app/page.tsx`** - Update scanWebsite() to include date parameter

### Optional Enhancements:
6. **`frontend/app/page.tsx`** - Add date validation UI
7. **`backend/ocr_service.py`** - Add date-based image naming (if needed)

## 10. Risk Assessment

### `backend/main.py` - HIGH RISK
- **Risk**: 8/10
- **Reasoning**: Core API logic, modifying scanning workflow
- **Impact**: Could break existing website scanning functionality
- **Mitigation**: Extensive testing required, maintain backward compatibility

### `backend/ocr_service.py` - LOW RISK
- **Risk**: 3/10
- **Reasoning**: Only optional changes, OCR core functionality intact
- **Impact**: Minimal, only if date-based image naming implemented

### `frontend/app/page.tsx` - MEDIUM RISK
- **Risk**: 5/10
- **Reasoning**: Large file, UI changes only, stateless
- **Impact**: UI disruption if poorly implemented
- **Mitigation**: Follow existing patterns, maintain consistency

## 11. Migration Plan

### Phase 1: Backend Modifications
1. Update `WebsiteScanRequest` model in `backend/main.py`
2. Modify `_run_scan_job()` to use date for URL resolution
3. Update `_build_page_url()` for date-based URL patterns
4. Add input validation for date format

### Phase 2: Frontend Modifications
1. Add date selector component to scan-website section
2. Update `scanWebsite()` function to include date parameter
3. Add date validation and error handling
4. Update UI to show date in scan progress

### Phase 3: Testing
1. Test backward compatibility (no date provided)
2. Test date-based URL resolution
3. Test pagination with dates
4. Test edge cases (invalid dates, different website formats)

## 12. Summary

### Files That Would Need Changes:
1. **`backend/main.py`** - Core modifications for date support in scanning
2. **`frontend/app/page.tsx`** - UI changes for date selector and submission

### Files That Should NOT Be Touched:
1. **`backend/ocr_service.py`** - Core OCR functionality unchanged
2. **`backend/highlight_service.py`** - Core highlighting unchanged
3. **`backend/news_keywords.py`** - Core keyword catalog unchanged
4. **`frontend/app/layout.tsx`** - Layout unchanged
5. **`frontend/lib/utils.ts`** - Utility functions unchanged

### Estimated Implementation Steps for Phase 2:
1. **Days 1-2**: Backend modifications (scan-website endpoint, URL resolution)
2. **Days 3-4**: Frontend UI integration (date selector, API updates)
3. **Days 5-6**: Testing and validation (backward compatibility, new features)
4. **Day 7**: Documentation and deployment preparation

**Total Estimated Time**: 1 week for core implementation
**Risk Level**: Medium (primarily due to backend scanning workflow changes)
