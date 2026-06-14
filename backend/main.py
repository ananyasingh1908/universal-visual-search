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
import hashlib
import numpy as np
import cv2
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

def _build_path_page_url(base_url: str, page_number: int) -> str:
    parsed = urlparse(base_url)

    parts = parsed.path.rstrip("/").split("/")

    # replace last path segment (current page number)
    if parts and parts[-1].isdigit():
        parts[-1] = str(page_number)
    else:
        parts.append(str(page_number))

    new_path = "/".join(parts)

    return urlunparse(parsed._replace(path=new_path))

def _phash_from_bytes(img_bytes: bytes) -> int:
    try:
        arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0
        img = cv2.resize(img, (32, 32), interpolation=cv2.INTER_AREA)
        dct = cv2.dct(np.float32(img))
        dct_low = dct[:8, :8]
        med = float(np.median(dct_low))
        bits = (dct_low > med).flatten()
        phash = 0
        for b in bits:
            phash = (phash << 1) | int(bool(b))
        return int(phash)
    except Exception:
        return 0


def _hamming_distance(a: int, b: int) -> int:
    return bin((a or 0) ^ (b or 0)).count("1")


def _fingerprint_equal(a: dict, b: dict) -> bool:
    if a.get("html_hash") and b.get("html_hash") and a["html_hash"] == b["html_hash"]:
        return True
    a_imgs = set(a.get("img_urls", []))
    b_imgs = set(b.get("img_urls", []))
    if a_imgs and b_imgs and a_imgs == b_imgs:
        a_ph = a.get("phash", 0)
        b_ph = b.get("phash", 0)
        if a_ph and b_ph and _hamming_distance(a_ph, b_ph) <= 8:
            return True
    a_ph = a.get("phash", 0)
    b_ph = b.get("phash", 0)
    if a_ph and b_ph and _hamming_distance(a_ph, b_ph) <= 7:
        return True
    return False


async def _fingerprint_page_main(page) -> dict:
    try:
        data = await page.evaluate(
            """
            () => {
                const imgs = Array.from(document.querySelectorAll('img.page-image'));
                const sources = imgs.map(img => img.getAttribute('src') || img.getAttribute('src2') || img.getAttribute('data-src') || img.currentSrc || '').filter(Boolean);
                const links = Array.from(document.querySelectorAll('a[href]')).map(a => a.getAttribute('href') || '').filter(Boolean);
                const ids = Array.from(document.querySelectorAll('[id], [data-id]')).map(el => el.id || el.getAttribute('data-id') || '').filter(Boolean);
                const container = document.querySelector('.page, .viewer, .epaper, .page-wrapper') || document.body;
                const htmlSnippet = (container.innerHTML || '').slice(0, 8000);
                return {sources, links, ids, htmlSnippet};
            }
            """
        )
    except Exception:
        data = {"sources": [], "links": [], "ids": [], "htmlSnippet": ""}

    img_urls = list(dict.fromkeys(data.get("sources", [])))
    links = list(dict.fromkeys(data.get("links", [])))
    ids = list(dict.fromkeys(data.get("ids", [])))
    html_snippet = data.get("htmlSnippet", "") or ""
    html_hash = hashlib.sha256(html_snippet.encode("utf-8")).hexdigest() if html_snippet else ""

    phash = 0
    try:
        locator = page.locator('img.page-image')
        if await locator.count() > 0:
            elem = locator.first
            box = await elem.bounding_box()
            try:
                loaded = await elem.evaluate("el => !!(el.naturalWidth && el.naturalWidth > 20)")
            except Exception:
                loaded = False
            if not loaded:
                try:
                    await page.evaluate("() => { window.scrollTo(0, document.body.scrollHeight/2); }")
                    await page.wait_for_timeout(500)
                    loaded = await elem.evaluate("el => !!(el.naturalWidth && el.naturalWidth > 20)")
                except Exception:
                    loaded = False
            if loaded and box and box.get("width") and box.get("height"):
                clip = {"x": max(0, float(box["x"])), "y": max(0, float(box["y"])), "width": max(1, float(box["width"])), "height": max(1, float(box["height"]))}
                img_bytes = await page.screenshot(type="png", clip=clip)
            else:
                img_bytes = await page.screenshot(type="png", full_page=False)
        else:
            img_bytes = await page.screenshot(type="png", full_page=False)
        phash = _phash_from_bytes(img_bytes)
    except Exception:
        phash = 0

    return {"img_urls": img_urls, "links": links, "ids": ids, "html_hash": html_hash, "phash": phash}


async def _probe_pages(page, base_url: str) -> int:
    fingerprints: list[dict] = []
    max_probes = 40
    for n in range(1, max_probes + 1):
        page_url = _build_path_page_url(base_url, n)
        print(f"PROBING PAGE {n}")
        print(f"URL = {page_url}")
        try:
            resp = await page.goto(page_url, wait_until="domcontentloaded", timeout=20000)
        except Exception as e:
            print(f"Navigation error: {e}")
            break
        print("CURRENT URL:", page.url)
        if resp is None:
            print("NO RESPONSE")
            break
        print(f"STATUS = {resp.status}")
        if resp.status >= 400:
            print("HTTP ERROR")
            break

        # wait briefly for images to load
        try:
            await page.wait_for_function("() => Array.from(document.querySelectorAll('img.page-image')).some(i=>i.naturalWidth>20)", timeout=3000)
        except Exception:
            await page.wait_for_timeout(800)

        fp = await _fingerprint_page_main(page)
        print(f"FP imgs={len(fp.get('img_urls',[]))} phash={fp.get('phash',0)} html_hash_prefix={fp.get('html_hash','')[:8]}")

        if fingerprints and _fingerprint_equal(fp, fingerprints[-1]):
            print(f"PAGE {n} repeats previous page")
            return n - 1
        for prev in fingerprints:
            if _fingerprint_equal(fp, prev):
                print(f"PAGE {n} matches earlier page - stopping")
                return n - 1

        fingerprints.append(fp)

    print(f"TOTAL PAGES FOUND = {len(fingerprints)}")
    return len(fingerprints)

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

            parsed_url = urlparse(url)
            use_path_probing = (
                "/" in parsed_url.path and
                not parsed_url.query
            )

            if use_path_probing:
                total_pages = await _probe_pages(page, url)

            print("FINAL TOTAL PAGES =", total_pages)

            all_ocr_entries: list[dict] = []
            pages_scanned = 0
            page_screenshots: dict[str, str] = {}
            page_headlines: dict[str, str] = {}
            page_errors: list[str] = []
            loop = asyncio.get_running_loop()


            if use_path_probing:
                _jobs[job_id]["progress"]["total_pages"] = total_pages
                print("SCAN LOOP TOTAL PAGES =", total_pages)
                for page_num in range(1, total_pages + 1):
                    try:
                        page_url = _build_path_page_url(url, page_num)

                        print("USING SCAN LOOP A")
                        print(f"SCANNING PAGE {page_num}")

                        await page.goto(
                            page_url,
                            wait_until="domcontentloaded",
                            timeout=100000,
                        )

                        await page.wait_for_timeout(5000)

                        try:
                            

                            print("PAGE IMAGE FOUND")

                            imgs = page.locator("img.page-image")
                            count = await imgs.count()

                            for i in range(count):
                                src = await imgs.nth(i).get_attribute("src")
                                print(f"IMAGE {i} = {src}")

                            img_src = await imgs.nth(0).get_attribute("src")

                            print("IMG SRC:", img_src)
                            print("CURRENT URL:", page.url) 

                        except Exception as e:
                            print("PAGE IMAGE NOT FOUND:", e)

                        await page.wait_for_timeout(3000)

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
                            None,
                            run_ocr,
                            reader,
                            shot_path,
                            page_num,
                        )

                        all_ocr_entries.extend(ocr_entries)

                        headline_summary = summarize_headline(
                            ocr_entries
                        )   

                        if headline_summary["headline_text"]:
                            page_headlines[str(page_num)] = (
                                headline_summary["headline_text"]
                            )

                        pages_scanned += 1

                    except Exception as page_err:
                        if page_num == 1:
                            raise Exception(
                                f"Failed to load first page: {page_err}"
                            )
                        else:   
                            page_errors.append(
                                f"Page {page_num}: {page_err}"
                            )
                            continue

                    _jobs[job_id]["progress"]["current_page"] = pages_scanned

                    _jobs[job_id]["progress"]["words_extracted"] = (
                        count_words(all_ocr_entries)
                    )
            else:
                _jobs[job_id]["progress"]["total_pages"] = total_pages

                for page_num in range(1, total_pages + 1):
                    try:
                        if page_num > 1:
                            try:
                                next_url = _build_page_url(url, page_num)
                                print("USING SCAN LOOP B")
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
