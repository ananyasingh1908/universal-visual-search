import asyncio
import sys
import json
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID, uuid4
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.staticfiles import StaticFiles

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsProactorEventLoopPolicy()
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

app.mount(
    "/outputs",
    StaticFiles(directory=OUTPUTS_DIR),
    name="outputs",
)

app.mount(
    "/screenshots",
    StaticFiles(directory=SCREENSHOTS_DIR),
    name="screenshots",
)


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
    parsed_url = urlparse(request.url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise HTTPException(status_code=400, detail="Invalid URL")

    document_id = str(uuid4())

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    screenshot_path = SCREENSHOTS_DIR / f"{document_id}.png"

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()

            response = .goto(
                request.url,
                wait_until="networkidle",
                timeout=30000
            )

            if response is None:
                raise HTTPException(
                    status_code=502,
                    detail="No response received from website"
                )

            await page.screenshot(
                path=str(screenshot_path),
                full_page=False
            )

            await browser.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Website scan failed: {str(e)}"
        )

    result = process_image_document(
        reader,
        screenshot_path,
        document_id,
        DATA_DIR
    )

    result["screenshot_url"] = (
        f"http://127.0.0.1:8000/screenshots/{screenshot_path.name}"
    )

    return result

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
        "documents": documents
    }

@app.post("/search-all")
async def search_all(request: SearchRequest):

    keyword = request.keyword.strip().lower()

    if not keyword:
        raise HTTPException(
            status_code=400,
            detail="Keyword cannot be empty"
        )

    results = []

    for file in DATA_DIR.glob("*.json"):

        with file.open(
            "r",
            encoding="utf-8"
        ) as f:

            ocr_entries = json.load(f)

        matches = [
            entry
            for entry in ocr_entries
            if keyword in str(
                entry.get("text", "")
            ).lower()
        ]

        if matches:
            results.append({
                "document_id": file.stem,
                "total_matches": len(matches),
                "matches": matches
            })

    return {
        "keyword": request.keyword,
        "documents_found": len(results),
        "results": results
    }