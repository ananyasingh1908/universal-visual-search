import asyncio
import sys
import json
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID, uuid4

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

from fastapi import FastAPI, UploadFile, File, HTTPException
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from pydantic import BaseModel
import easyocr

from highlight_service import (
    DocumentNotFoundError,
    ImageReadError,
    OriginalImageNotFoundError,
    highlight_keyword,
)
from ocr_service import process_image_document

app = FastAPI()

reader = easyocr.Reader(['en'])
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"


class SearchRequest(BaseModel):
    document_id: str
    keyword: str


class HighlightRequest(BaseModel):
    document_id: str
    keyword: str


class WebsiteScanRequest(BaseModel):
    url: str


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
        "matches": matches
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
        return highlight_keyword(document_id, keyword, BASE_DIR)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except OriginalImageNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ImageReadError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/scan-website")
async def scan_website(request: WebsiteScanRequest):

    print("STEP 1")

    parsed_url = urlparse(request.url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise HTTPException(status_code=400, detail="Invalid URL")

    print("STEP 2")

    document_id = str(uuid4())

    print("STEP 3")

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    screenshot_path = SCREENSHOTS_DIR / f"{document_id}.png"

    print("STEP 4")

    try:
        async with async_playwright() as playwright:

            print("STEP 5")

            browser = await playwright.chromium.launch(headless=True)

            print("STEP 6")

            page = await browser.new_page()

            print("STEP 7")

            response = await page.goto(
                request.url,
                wait_until="networkidle",
                timeout=30000
            )

            print("STEP 8")

            if response is None:
                raise HTTPException(
                    status_code=502,
                    detail="No response received from website"
                )

            print("STEP 9")

            await page.screenshot(
                path=str(screenshot_path),
                full_page=True
            )

            print("STEP 10")

            await browser.close()

    except Exception as e:
        print("SCAN WEBSITE ERROR:")
        print(repr(e))
        raise

    print("STEP 11")

    return process_image_document(
        reader,
        screenshot_path,
        document_id,
        DATA_DIR
    )