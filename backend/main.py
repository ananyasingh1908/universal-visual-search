import asyncio
import sys
import json
from pathlib import Path
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from uuid import UUID, uuid4
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsProactorEventLoopPolicy()
    )

from fastapi import FastAPI, UploadFile, File, HTTPException
from playwright.async_api import async_playwright
from pydantic import BaseModel
import easyocr

from highlight_service import (
    DocumentNotFoundError,
    ImageReadError,
    OriginalImageNotFoundError,
    highlight_keyword,
)
from ocr_service import (
    process_image_document,
    run_ocr,
    save_ocr_output,
    count_words,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

reader = easyocr.Reader(['en'])
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
OUTPUTS_DIR = BASE_DIR / "outputs"

app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")
app.mount("/screenshots", StaticFiles(directory=SCREENSHOTS_DIR), name="screenshots")

SCREENSHOT_BASE_URL = "/screenshots"
OUTPUT_BASE_URL = "/outputs"


class SearchRequest(BaseModel):
    document_id: str
    keyword: str


class HighlightRequest(BaseModel):
    document_id: str
    keyword: str
    page_number: int | None = None


class WebsiteScanRequest(BaseModel):
    url: str


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

    return process_image_document(reader, upload_path, document_id, DATA_DIR)


@app.post("/search")
async def search_document(request: SearchRequest):
    try:
        document_id = str(UUID(request.document_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document_id")

    keyword = request.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")

    document_path = DATA_DIR / f"{document_id}.json"
    if not document_path.is_file():
        raise HTTPException(status_code=404, detail="Document not found")

    with document_path.open("r", encoding="utf-8") as f:
        ocr_entries = json.load(f)

    keyword_lower = keyword.lower()
    matches = [
        entry
        for entry in ocr_entries
        if keyword_lower in str(entry.get("text", "")).lower()
    ]

    return {
        "document_id": document_id,
        "keyword": keyword,
        "total_matches": len(matches),
        "matches": matches,
    }


@app.post("/highlight")
async def highlight_document(request: HighlightRequest):
    try:
        document_id = str(UUID(request.document_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document_id")

    keyword = request.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")

    try:
        return highlight_keyword(
            document_id, keyword, BASE_DIR,
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


async def _run_scan_job(job_id: str, url: str):
    document_id = str(uuid4())
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        _jobs[job_id]["status"] = "processing"

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
                        path=str(shot_path), full_page=False

                        print("Saved:", shot_path)
                        print("Exists:", shot_path.exists())
                    )
                    

                    page_screenshots[str(page_num)] = (
                        f"{SCREENSHOT_BASE_URL}/{shot_name}"
                    )

                    ocr_entries = await loop.run_in_executor(
                        None, run_ocr, reader, shot_path, page_num,
                    )
                    all_ocr_entries.extend(ocr_entries)
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
        }

    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)


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
    keyword = request.keyword.strip().lower()
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")

    results = []
    for file in DATA_DIR.glob("*.json"):
        with file.open("r", encoding="utf-8") as f:
            ocr_entries = json.load(f)

        matches = [
            entry
            for entry in ocr_entries
            if keyword in str(entry.get("text", "")).lower()
        ]

        if matches:
            results.append({
                "document_id": file.stem,
                "total_matches": len(matches),
                "matches": matches,
            })

    return {
        "keyword": request.keyword,
        "documents_found": len(results),
        "results": results,
    }
