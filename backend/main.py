import asyncio
import logging
import os
import sys
import json
from pathlib import Path
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from uuid import UUID, uuid4
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from fastapi import FastAPI, UploadFile, File, HTTPException
from playwright.async_api import async_playwright
from pydantic import BaseModel

from highlight_service import (
    DocumentNotFoundError,
    ImageReadError,
    OriginalImageNotFoundError,
    highlight_keywords,
)
from lokmat_scraper import scrape_lokmat_times_edition
from newspaper_resolver import resolve_newspaper_url
from news_keywords import first_matching_keyword, get_news_keywords
from ocr_service import (
    process_image_document,
    run_ocr,
    save_ocr_output,
    count_words,
    summarize_headline,
)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    policy = asyncio.get_event_loop_policy()
    # Log event loop policy and whether subprocess support exists
    print("startup loop policy", type(policy).__name__, policy)
    loop = asyncio.get_running_loop()
    print("startup loop type", type(loop).__name__)
    print("startup supports subprocess", hasattr(loop, "subprocess_exec"))

    # Configure basic logging if not already configured
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("backend.startup")

    api_key = os.getenv("GOOGLE_CLOUD_VISION_API_KEY", "").strip()
    if api_key:
        logger.info("Google Vision API key detected in environment")
        logger.info("OCR requests will be sent to Google Vision API")
    else:
        logger.warning("Google Vision API key NOT found; falling back to EasyOCR")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

reader = None
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
OUTPUTS_DIR = BASE_DIR / "outputs"

SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")
app.mount("/screenshots", StaticFiles(directory=SCREENSHOTS_DIR), name="screenshots")

SCREENSHOT_BASE_URL = "http://127.0.0.1:8000/screenshots"
OUTPUT_BASE_URL = "/outputs"


class SearchRequest(BaseModel):
    document_id: str
    keyword: str | None = None


class HighlightRequest(BaseModel):
    document_id: str
    keyword: str | None = None
    page_number: int | None = None


class WebsiteScanRequest(BaseModel):
    url: str


class NewspaperScanRequest(BaseModel):
    newspaper: str
    date: str
    page: int = 1


class LokmatScrapeRequest(BaseModel):
    edition_name: str
    date: str


_jobs: dict[str, dict] = {}


@app.post("/ocr")
async def extract_text(file: UploadFile = File(...)):
    image_bytes = await file.read()
    document_id = str(uuid4())
    file_extension = Path(file.filename or "").suffix or ".jpg"

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    upload_path = UPLOADS_DIR / f"{document_id}{file_extension}"
    with upload_path.open("wb") as f:
        f.write(image_bytes)

    return await asyncio.to_thread(
        process_image_document,
        reader,
        upload_path,
        document_id,
        DATA_DIR,
    )


@app.post("/search")
async def search_document(request: SearchRequest):
    try:
        document_id = str(UUID(request.document_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document_id")

    document_path = DATA_DIR / f"{document_id}.json"
    if not document_path.is_file():
        raise HTTPException(status_code=404, detail="Document not found")

    with document_path.open("r", encoding="utf-8") as f:
        ocr_entries = json.load(f)

    keywords = get_news_keywords()
    matches = []
    for entry in ocr_entries:
        matched_keyword = first_matching_keyword(str(entry.get("text", "")), keywords)
        if not matched_keyword:
            continue
        matches.append({
            **entry,
            "matched_keyword": matched_keyword,
        })

    return {
        "document_id": document_id,
        "keyword": "predefined keyword set",
        "keywords": list(keywords),
        "total_matches": len(matches),
        "matches": matches,
    }


@app.post("/highlight")
async def highlight_document(request: HighlightRequest):
    try:
        document_id = str(UUID(request.document_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document_id")

    try:
        return highlight_keywords(
            document_id,
            list(get_news_keywords()),
            BASE_DIR,
            page_number=request.page_number,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except OriginalImageNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ImageReadError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


async def _detect_total_pages(page) -> int:
    return await page.evaluate("""
        () => {
            let maxPage = 1;

            const links = document.querySelectorAll(
                'a[href*="page="], a[href*="pg="], a[href*="p="], a[href*="Page="]'
            );
            links.forEach(link => {
                const href = link.getAttribute('href') || '';
                const m = href.match(/[?&](?:page|pg|p)=(\\d+)/i);
                if (m) { const n = parseInt(m[1], 10); if (n > maxPage) maxPage = n; }
            });

            const bodyText = document.body ? (document.body.innerText || '') : '';
            const ofMatch = bodyText.match(
                /(?:page|pg)s?\\s*\\d+\\s*(?:of|\\/)\\s*(\\d+)/i
            );
            if (ofMatch) {
                const n = parseInt(ofMatch[1], 10);
                if (n > maxPage) maxPage = n;
            }

            document.querySelectorAll(
                '[data-page], [data-pagenumber], [data-page-number], [data-pages]'
            ).forEach(el => {
                const v = el.getAttribute('data-pages')
                    || el.getAttribute('data-page')
                    || el.getAttribute('data-pagenumber')
                    || el.getAttribute('data-page-number') || '';
                const n = parseInt(v, 10);
                if (!isNaN(n) && n > maxPage) maxPage = n;
            });

            document.querySelectorAll(
                'select[aria-label*="page" i], select[aria-label*="pagination" i]'
            ).forEach(sel => {
                Array.from(sel.options).forEach(opt => {
                    const n = parseInt(opt.value, 10);
                    if (!isNaN(n) && n > maxPage) maxPage = n;
                });
            });

            const pageIndicators = document.querySelectorAll(
                '.thumbnails .item, .page-indicator, [class*="page-thumb"], ' +
                '[class*="page_thumb"], .owl-item .item'
            );
            const indicatorCount = pageIndicators.length;
            if (indicatorCount > maxPage) maxPage = indicatorCount;

            const h1Numbers = document.querySelectorAll(
                '.thumbnails .item h1, .page-indicator h1, ' +
                '[class*="page-thumb"] h1, [class*="page_thumb"] h1'
            );
            h1Numbers.forEach(h1 => {
                const n = parseInt((h1.innerText || '').trim(), 10);
                if (!isNaN(n) && n > maxPage) maxPage = n;
            });

            return maxPage;
        }
    """)


def _build_page_url(base_url: str, page_number: int) -> str:
    parsed = urlparse(base_url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    page_param = None
    for name in ['page', 'pg', 'p', 'Page']:
        if name in params:
            page_param = name
            break

    if page_param:
        params[page_param] = [str(page_number)]
    else:
        params['page'] = [str(page_number)]

    new_query = urlencode(params, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


@app.post("/scan-website")
async def scan_website(request: WebsiteScanRequest):
    parsed_url = urlparse(request.url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise HTTPException(status_code=400, detail="Invalid URL")

    job_id = str(uuid4())
    _jobs[job_id] = {
        "status": "pending",
        "progress": {
            "current_page": 0,
            "total_pages": 0,
            "words_extracted": 0,
        },
        "result": None,
        "error": None,
    }

    asyncio.create_task(_run_scan_job(job_id, request.url))
    
    return {"job_id": job_id, "status": "pending"}


@app.get("/scan-website/status/{job_id}")
async def scan_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resp = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
    }
    if job["status"] == "completed" and job["result"]:
        resp["result"] = job["result"]
    if job["status"] == "failed":
        resp["error"] = job["error"]

    return resp


@app.post("/resolve-and-scan")
async def resolve_and_scan(request: NewspaperScanRequest):
    from newspaper_resolver import resolve_newspaper_url
    try:
        print(f"resolve_and_scan: Processing request - newspaper: {request.newspaper}, date: {request.date}, page: {request.page}")
        resolved_url = resolve_newspaper_url(request.newspaper, request.date, request.page)
        print(f"resolve_and_scan: Generated URL: {resolved_url}")
        return await scan_website(WebsiteScanRequest(url=resolved_url))
    except Exception as e:
        print(f"resolve_and_scan: Failed to resolve newspaper URL: {e}")
        import traceback
        print(f"resolve_and_scan: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve newspaper URL: {e}")


async def _run_scan_job(job_id: str, url: str):
    document_id = str(uuid4())
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    import asyncio
    try:
        _jobs[job_id]["status"] = "processing"

        print("=== PLAYWRIGHT DEBUG ===")
        print("POLICY:", type(asyncio.get_event_loop_policy()).__name__)
        print("LOOP:", type(asyncio.get_running_loop()).__name__)
        print("========================")

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            response = await page.goto(
                url, wait_until="domcontentloaded", timeout=30000,
            )
            if response is None:
                raise Exception("No response received from website")

            total_pages = max(1, await _detect_total_pages(page))

            _jobs[job_id]["progress"]["total_pages"] = total_pages

            all_ocr_entries: list[dict] = []
            pages_scanned = 0
            page_screenshots: dict[str, str] = {}
            page_headlines: dict[str, str] = {}
            page_errors: list[str] = []
            loop = asyncio.get_running_loop()

            for page_num in range(1, total_pages + 1):
                try:
                    if page_num > 1:
                        try:
                            next_url = _build_page_url(url, page_num)
                            await page.goto(
                                next_url,
                                wait_until="domcontentloaded",
                                timeout=100000,
                            )
                            await page.wait_for_timeout(10000)
                        except Exception as nav_err:
                            print(f"Page {page_num} failed: {nav_err}")
                            page_errors.append(
                                f"Page {page_num}: navigation failed ({nav_err})"
                            )
                            continue

                    shot_name = f"{document_id}_p{page_num}.png"
                    shot_path = SCREENSHOTS_DIR / shot_name
                    await page.screenshot(
                        path=str(shot_path),
                        full_page=True,
                    )

                    print("Saved:", shot_path)
                    print("Exists:", shot_path.exists())

                    page_screenshots[str(page_num)] = (
                        f"{SCREENSHOT_BASE_URL}/{shot_name}"
                    )

                    ocr_entries = await loop.run_in_executor(
                        None, run_ocr, reader, shot_path, page_num,
                    )
                    all_ocr_entries.extend(ocr_entries)
                    headline_summary = summarize_headline(ocr_entries)
                    if headline_summary["headline_text"]:
                        page_headlines[str(page_num)] = headline_summary["headline_text"]
                    pages_scanned += 1

                except Exception as page_err:
                    page_errors.append(
                        f"Page {page_num}: {page_err}"
                    )
                    continue

                _jobs[job_id]["progress"]["current_page"] = pages_scanned
                _jobs[job_id]["progress"]["words_extracted"] = count_words(
                    all_ocr_entries
                )

            await browser.close()

        if pages_scanned == 0:
            error_detail = "; ".join(page_errors) if page_errors else "No pages scanned"
            raise Exception(error_detail)

        save_ocr_output(document_id, all_ocr_entries, DATA_DIR)
        total_words = count_words(all_ocr_entries)

        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["result"] = {
            "document_id": document_id,
            "pages_scanned": pages_scanned,
            "total_pages": total_pages,
            "total_words": total_words,
            "screenshots": page_screenshots,
            "screenshot_url": page_screenshots.get("1", ""),
            "page_headlines": page_headlines,
            "headline_text": page_headlines.get("1", "")
                or next(iter(page_headlines.values()), ""),
        }

    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)


@app.post("/scrape-lokmat-times")
async def scrape_lokmat_times(request: LokmatScrapeRequest):
    edition_name = request.edition_name.strip()
    date_value = request.date.strip()

    if not edition_name:
        raise HTTPException(status_code=400, detail="edition_name is required")

    job_id = str(uuid4())
    _jobs[job_id] = {
        "status": "pending",
        "progress": {
            "current_page": 0,
            "total_pages": 0,
            "words_extracted": 0,
        },
        "result": None,
        "error": None,
    }

    asyncio.create_task(
        _run_lokmat_scrape_job(job_id, edition_name, date_value)
    )

    return {"job_id": job_id, "status": "pending"}


@app.get("/scrape-lokmat-times/status/{job_id}")
async def scrape_lokmat_times_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    response = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
    }
    if job["status"] == "completed" and job["result"]:
        response["result"] = job["result"]
    if job["status"] == "failed":
        response["error"] = job["error"]

    return response


async def _run_lokmat_scrape_job(job_id: str, edition_name: str, date_value: str):
    try:
        _jobs[job_id]["status"] = "processing"

        result = await scrape_lokmat_times_edition(
            edition=edition_name,
            date_value=date_value,
            base_dir=BASE_DIR,
            reader=reader,
            keywords=get_news_keywords(),
            newspaper_name="Lokmat Times",
        )

        payload = result["result"]
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["result"] = payload
        _jobs[job_id]["progress"] = {
            "current_page": payload.get("pages_scanned", 0),
            "total_pages": payload.get("total_pages_detected", 0),
            "words_extracted": sum(
                len(article.get("article_text", "").split())
                for article in payload.get("results", [])
            ),
        }
    except Exception as exc:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(exc)


@app.get("/documents")
async def get_documents():
    documents = []
    DATA_DIR.mkdir(exist_ok=True)
    for file in DATA_DIR.glob("*.json"):
        documents.append({
            "document_id": file.stem,
            "filename": file.name,
        })
    return {
        "total_documents": len(documents),
        "documents": documents,
    }


@app.post("/search-all")
async def search_all(request: SearchRequest):
    keywords = get_news_keywords()
    results = []
    print("OCR RESULTS COUNT:", len(results))

    all_text = " ".join([r[1] for r in results if len(r) > 1])

    print("Total OCR text length:", len(all_text))
    print("First 500 chars:")
    print(all_text[:500])
    for file in DATA_DIR.glob("*.json"):
        with file.open("r", encoding="utf-8") as f:
            ocr_entries = json.load(f)

        matches = []
        for entry in ocr_entries:
            matched_keyword = first_matching_keyword(str(entry.get("text", "")), keywords)
            if not matched_keyword:
                continue
            matches.append({
                **entry,
                "matched_keyword": matched_keyword,
            })

        if matches:
            results.append({
                "document_id": file.stem,
                "total_matches": len(matches),
                "matches": matches,
            })

    return {
        "keyword": "predefined keyword set",
        "keywords": list(keywords),
        "documents_found": len(results),
        "results": results,
    }
print("=== REGISTERED ROUTES ===")

for route in app.routes:
    print(route.path)
