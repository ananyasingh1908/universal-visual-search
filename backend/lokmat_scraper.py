from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import date as date_cls
from pathlib import Path
from typing import Iterable
from urllib.parse import quote
from uuid import uuid4

import cv2
import hashlib
import io
import numpy as np
from playwright.async_api import async_playwright

from news_keywords import (
    get_news_keywords,
    keyword_matches_text,
)
from ocr_service import run_ocr, save_ocr_output, summarize_headline

SCREENSHOT_BASE_URL = "http://127.0.0.1:8000/screenshots"
OUTPUT_BASE_URL = "http://127.0.0.1:8000/outputs"
MAX_PAGES = 300


@dataclass
class LokmatScrapeResult:
    newspaper: str
    edition: str
    date: str
    pages_scanned: int
    total_pages_detected: int
    results: list[dict]


def build_lokmat_page_url(
    base_url: str,
    edition: str,
    date_value: str,
    page_number: int,
) -> str:
    encoded_edition = quote(_normalize_text(edition), safe="")
    normalized_base_url = base_url.rstrip("/")
    return f"{normalized_base_url}/{encoded_edition}/{date_value}/{page_number}"


async def scrape_lokmat_times_edition(
    edition: str,
    date_value: str,
    base_dir: Path,
    reader,
    keywords: Iterable[str] | None = None,
    newspaper_name: str = "Lokmat Times",
) -> dict:
    _validate_date(date_value)

    keyword_list = tuple(keywords) if keywords is not None else get_news_keywords()
    if not keyword_list:
        keyword_list = get_news_keywords()

    job_id = str(uuid4())
    raw_entries: list[dict] = []
    collected_results: list[dict] = []

    screenshots_dir = base_dir / "screenshots"
    outputs_dir = base_dir / "outputs"
    data_dir = base_dir / "data"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        base_url = None
        page_1_total_pages = 0
        pages_scanned = 0

        try:
            base_url = await _resolve_base_url(
                page=page,
                edition=edition,
                date_value=date_value,
            )

            # Probe pages to detect total pages robustly before scanning.
            probed = await _probe_pages(
                page=page,
                base_url=base_url,
                edition=edition,
                date_value=date_value,
                max_probe=MAX_PAGES,
            )
            if probed:
                page_1_total_pages = probed

            # Use probed value when available, otherwise fallback to scanning up to MAX_PAGES
            max_scan = page_1_total_pages if page_1_total_pages else MAX_PAGES
            for page_number in range(1, max_scan + 1):
                page_url = build_lokmat_page_url(
                    base_url,
                    edition,
                    date_value,
                    page_number,
                )
                response = await page.goto(
                    page_url,
                    wait_until="domcontentloaded",
                    timeout=20000,
                )
                if response is None:
                    break
                if response.status >= 400:
                    break

                # Wait for images to appear (short, with fallback)
                try:
                    await page.wait_for_selector('img.page-image', timeout=6000)
                except Exception:
                    await page.wait_for_timeout(1200)

                # Trigger lazy-loading if necessary
                try:
                    await page.evaluate("() => { window.scrollTo(0, document.body.scrollHeight/2); }")
                    await page.wait_for_timeout(500)
                except Exception:
                    pass

                if await _looks_like_missing_page(page, page_number):
                    break

                shot_name = f"{job_id}_p{page_number}.png"
                shot_path = screenshots_dir / shot_name
                await page.screenshot(path=str(shot_path), full_page=True)

                page_ocr_entries = await asyncio.to_thread(
                    run_ocr,
                    reader,
                    shot_path,
                    page_number,
                )
                raw_entries.extend(page_ocr_entries)
                pages_scanned += 1

                # If probing didn't find a total, try the page-detected total on page 1
                if page_number == 1 and not page_1_total_pages:
                    page_1_total_pages = await _detect_total_pages(page)

                page_results = _extract_matched_articles_from_page(
                    ocr_entries=page_ocr_entries,
                    screenshot_path=shot_path,
                    page_url=page_url,
                    page_number=page_number,
                    edition=edition,
                    date_value=date_value,
                    newspaper_name=newspaper_name,
                    keywords=keyword_list,
                    outputs_dir=outputs_dir,
                )
                collected_results.extend(page_results)

                if page_1_total_pages and page_number >= page_1_total_pages:
                    # If the page declares a total and we've reached it, verify the next page
                    next_url = build_lokmat_page_url(
                        base_url,
                        edition,
                        date_value,
                        page_number + 1,
                    )
                    next_response = await page.goto(
                        next_url,
                        wait_until="domcontentloaded",
                        timeout=15000,
                    )
                    if next_response is None or next_response.status >= 400:
                        break
                    try:
                        await page.wait_for_selector('img.page-image', timeout=6000)
                    except Exception:
                        await page.wait_for_timeout(1000)
                    if await _looks_like_missing_page(page, page_number + 1):
                        break
                    continue

            save_ocr_output(job_id, raw_entries, data_dir)
        finally:
            await browser.close()

    result_payload = {
        "newspaper": newspaper_name,
        "edition": _normalize_text(edition),
        "date": date_value,
        "pages_scanned": pages_scanned,
        "total_pages_detected": page_1_total_pages,
        "results": collected_results,
    }

    return {
        "job_id": job_id,
        "status": "completed",
        "result": result_payload,
        "base_url": base_url,
    }


async def _resolve_base_url(page, edition: str, date_value: str) -> str:
    candidates = [
        "https://epaper.lokmat.com/lokmattimes/main-editions",
        "https://epaper.lokmat.com/main-editions",
    ]

    encoded_edition = quote(_normalize_text(edition), safe="")
    first_page = f"{encoded_edition}/{date_value}/1"

    for base in candidates:
        url = f"{base}/{first_page}"
        response = await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=20000,
        )
        if response is None or response.status >= 400:
            continue
        await page.wait_for_timeout(8000)
        if await _looks_like_missing_page(page, 1):
            continue
        return base

    raise RuntimeError("Could not open the Lokmat Times edition page")


async def _looks_like_missing_page(page, page_number: int) -> bool:
    title = _normalize_text(await page.title())
    body_text = _normalize_text(await page.evaluate(
        """() => document.body ? (document.body.innerText || '') : ''"""
    ))

    missing_markers = (
        "page not found",
        "not found",
        "404",
        "no records found",
        "something went wrong",
        "error",
        "invalid",
    )
    if any(marker in title.casefold() for marker in missing_markers):
        return True
    if any(marker in body_text.casefold() for marker in missing_markers):
        return True

    if not body_text:
        return True

    page_marker = str(page_number)
    if page_number > 1 and page_marker not in body_text:
        # If the navigation page does not mention the page number at all, we
        # still allow it through when OCR finds content. This is only a soft
        # guard, not a hard failure.
        return False

    return False


async def _detect_total_pages(page) -> int:
    return await page.evaluate(
        """
        () => {
            let maxPage = 0;

            const candidates = document.querySelectorAll(
                'a, button, li, span, div'
            );
            candidates.forEach((el) => {
                const text = (el.innerText || el.textContent || '').trim();
                if (!text) return;

                const href = el.getAttribute && el.getAttribute('href');
                if (href) {
                    const hrefMatch = href.match(/(?:page|pg|p)=(\\d+)/i)
                        || href.match(/\\/(\\d+)(?:\\/?$)/);
                    if (hrefMatch) {
                        const n = parseInt(hrefMatch[1], 10);
                        if (!Number.isNaN(n) && n > maxPage) maxPage = n;
                    }
                }

                const textMatch = text.match(/\\b(\\d{1,3})\\b/g);
                if (textMatch) {
                    textMatch.forEach((num) => {
                        const n = parseInt(num, 10);
                        if (!Number.isNaN(n) && n > maxPage && n <= 300) {
                            maxPage = n;
                        }
                    });
                }
            });

            const bodyText = document.body ? (document.body.innerText || '') : '';
            const pageRegexes = [
                /(?:page|pg)\\s*(\\d+)\\s*(?:of|\\/)?\\s*(\\d+)/i,
                /\\b(\\d+)\\s*\\/\\s*(\\d+)\\b/i,
            ];
            pageRegexes.forEach((regex) => {
                const match = bodyText.match(regex);
                if (match) {
                    const n = parseInt(match[2] || match[1], 10);
                    if (!Number.isNaN(n) && n > maxPage) maxPage = n;
                }
            });

            document.querySelectorAll('[data-page], [data-page-number], [data-pagenumber], [data-pages]').forEach((el) => {
                const attrs = [
                    el.getAttribute('data-page'),
                    el.getAttribute('data-page-number'),
                    el.getAttribute('data-pagenumber'),
                    el.getAttribute('data-pages'),
                ].filter(Boolean);
                attrs.forEach((value) => {
                    const n = parseInt(value, 10);
                    if (!Number.isNaN(n) && n > maxPage) maxPage = n;
                });
            });

            return maxPage;
        }
        """
    )


# --- Fingerprint & probing helpers

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
    # Prefer deterministic HTML snippet/hash match
    if a.get("html_hash") and b.get("html_hash") and a["html_hash"] == b["html_hash"]:
        return True

    # If image URL sets match and perceptual hashes are close, treat as equal
    a_imgs = set(a.get("img_urls", []))
    b_imgs = set(b.get("img_urls", []))
    if a_imgs and b_imgs and a_imgs == b_imgs:
        a_ph = a.get("phash", 0)
        b_ph = b.get("phash", 0)
        if a_ph and b_ph and _hamming_distance(a_ph, b_ph) <= 6:
            return True
        # fallback to link equality
        if set(a.get("links", [])) == set(b.get("links", [])):
            return True

    # Perceptual hash similarity alone is a strong indicator
    a_ph = a.get("phash", 0)
    b_ph = b.get("phash", 0)
    if a_ph and b_ph and _hamming_distance(a_ph, b_ph) <= 5:
        return True

    return False


async def _fingerprint_page(page) -> dict:
    # Collect image urls, link hrefs and a short HTML snippet
    try:
        data = await page.evaluate(
            """
            () => {
                const imgs = Array.from(document.querySelectorAll('img.page-image'));
                const sources = imgs.map(img =>
                    img.getAttribute('src') || img.getAttribute('src2') || img.getAttribute('data-src') || img.currentSrc || ''
                ).filter(Boolean);
                const links = Array.from(document.querySelectorAll('a[href]')).map(a => a.getAttribute('href') || '').filter(Boolean);
                const ids = Array.from(document.querySelectorAll('[id], [data-id]')).map(el => el.id || el.getAttribute('data-id') || '').filter(Boolean);
                const container = document.querySelector('.page, .viewer, .epaper, .page-wrapper') || document.body;
                const htmlSnippet = (container.innerHTML || '').slice(0, 20000);
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

    # Try to capture a small screenshot of the first page image to compute phash
    phash = 0
    try:
        locator = page.locator('img.page-image')
        if await locator.count() > 0:
            elem = locator.first
            box = await elem.bounding_box()

            # Prefer to ensure the image has actually loaded (naturalWidth)
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
                clip = {
                    "x": max(0, float(box["x"])),
                    "y": max(0, float(box["y"])),
                    "width": max(1, float(box["width"])),
                    "height": max(1, float(box["height"])),
                }
                img_bytes = await page.screenshot(type="png", clip=clip)
            else:
                img_bytes = await page.screenshot(type="png", full_page=False)
        else:
            img_bytes = await page.screenshot(type="png", full_page=False)
        phash = _phash_from_bytes(img_bytes)
    except Exception:
        phash = 0

    return {
        "img_urls": img_urls,
        "links": links,
        "ids": ids,
        "html_hash": html_hash,
        "phash": phash,
    }


async def _probe_pages(page, base_url: str, edition: str, date_value: str, max_probe: int = 100) -> int:
    fingerprints: list[dict] = []
    for n in range(1, max_probe + 1):
        url = build_lokmat_page_url(base_url, edition, date_value, n)
        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        except Exception:
            break
        if resp is None:
            break

        # Wait for at least one real image to load (naturalWidth > 20).
        # Try a few attempts, nudging the page to trigger lazy-loading.
        loaded = False
        for _attempt in range(3):
            try:
                await page.wait_for_function(
                    "() => Array.from(document.querySelectorAll('img.page-image')).some(img => img.naturalWidth && img.naturalWidth > 20)",
                    timeout=2500,
                )
                loaded = True
                break
            except Exception:
                try:
                    await page.evaluate("() => { window.scrollTo(0, document.body.scrollHeight/2); }")
                except Exception:
                    pass
                await page.wait_for_timeout(800)
        if not loaded:
            # final short wait as a fallback
            await page.wait_for_timeout(800)

        fp = await _fingerprint_page(page)

        # If identical to previous page, treat as repetition and stop
        if fingerprints and _fingerprint_equal(fp, fingerprints[-1]):
            return n - 1

        # If matches any earlier page, stop (cycle/repeat)
        for prev in fingerprints:
            if _fingerprint_equal(fp, prev):
                return n - 1

        fingerprints.append(fp)

    return len(fingerprints)


# --- Extraction & OCR helpers (restored original logic)

def _extract_matched_articles_from_page(
    ocr_entries: list[dict],
    screenshot_path: Path,
    page_url: str,
    page_number: int,
    edition: str,
    date_value: str,
    newspaper_name: str,
    keywords: Iterable[str],
    outputs_dir: Path,
) -> list[dict]:
    article_blocks = _group_ocr_into_articles(ocr_entries)
    page_headline = summarize_headline(ocr_entries).get("headline_text", "")
    matches: list[dict] = []

    for article_index, block in enumerate(article_blocks, start=1):
        article_text = _compose_article_text(block["title_lines"], block["body_lines"])
        if not article_text:
            continue

        matched_keywords = _collect_matched_keywords(article_text, keywords)
        if not matched_keywords:
            continue

        title = _clean_article_title(block["title_lines"], block["body_lines"], page_headline)
        image_url = _crop_article_image(
            screenshot_path=screenshot_path,
            entries=block["entries"],
            outputs_dir=outputs_dir,
            page_number=page_number,
            article_index=article_index,
        )

        matches.append({
            "newspaper": newspaper_name,
            "edition": _normalize_text(edition),
            "date": date_value,
            "page": page_number,
            "title": title,
            "matched_keywords": matched_keywords,
            "source_url": page_url,
            "image_url": image_url,
            "article_text": article_text,
        })

    return matches


def _group_ocr_into_articles(ocr_entries: list[dict]) -> list[dict]:
    if not ocr_entries:
        return []

    median_height = max(1.0, _median_height(ocr_entries))
    lines = _group_entries_into_lines(ocr_entries, median_height)

    articles: list[dict] = []
    current: dict | None = None

    for line in lines:
        if line["is_headline"]:
            if current and (current["title_lines"] or current["body_lines"]):
                articles.append(current)
            current = {
                "title_lines": [line],
                "body_lines": [],
                "entries": list(line["entries"]),
            }
            continue

        if current is None:
            current = {
                "title_lines": [],
                "body_lines": [line],
                "entries": list(line["entries"]),
            }
        else:
            current["body_lines"].append(line)
            current["entries"].extend(line["entries"])

    if current and (current["title_lines"] or current["body_lines"]):
        articles.append(current)

    return articles


def _group_entries_into_lines(entries: list[dict], median_height: float) -> list[dict]:
    tolerance = max(12.0, median_height * 0.85)
    clusters: list[dict] = []

    for entry in sorted(entries, key=lambda item: (_entry_rect(item) or (0, 0, 0, 0))[1]):
        rect = _entry_rect(entry)
        if rect is None:
            continue

        x1, y1, x2, y2 = rect
        center_y = (y1 + y2) / 2.0
        placed = False

        for cluster in clusters:
            if abs(center_y - cluster["center_y"]) <= tolerance:
                count = len(cluster["entries"])
                cluster["entries"].append(entry)
                cluster["center_y"] = ((cluster["center_y"] * count) + center_y) / (count + 1)
                cluster["top"] = min(cluster["top"], y1)
                cluster["bottom"] = max(cluster["bottom"], y2)
                cluster["left"] = min(cluster["left"], x1)
                cluster["right"] = max(cluster["right"], x2)
                placed = True
                break

        if not placed:
            clusters.append({
                "entries": [entry],
                "center_y": center_y,
                "top": y1,
                "bottom": y2,
                "left": x1,
                "right": x2,
            })

    lines: list[dict] = []
    for cluster in clusters:
        line_entries = sorted(cluster["entries"], key=lambda item: (_entry_rect(item) or (0, 0, 0, 0))[0])
        line_text = " ".join(_normalize_text(entry.get("text", "")) for entry in line_entries).strip()
        lines.append({
            "entries": line_entries,
            "text": line_text,
            "top": cluster["top"],
            "bottom": cluster["bottom"],
            "left": cluster["left"],
            "right": cluster["right"],
            "is_headline": any(bool(entry.get("is_headline")) for entry in line_entries),
        })

    return sorted(lines, key=lambda item: (item["top"], item["left"]))


def _compose_article_text(title_lines: list[dict], body_lines: list[dict]) -> str:
    ordered_lines = title_lines + body_lines
    if not ordered_lines:
        return ""

    raw_text = "\n".join(_normalize_text(line.get("text", "")) for line in ordered_lines)
    raw_text = re.sub(r"(\w)-\n(\w)", r"\1\2", raw_text)
    raw_text = re.sub(r"\n{3,}", "\n\n", raw_text)
    return raw_text.strip()


def _clean_article_title(
    title_lines: list[dict],
    body_lines: list[dict],
    page_headline: str,
) -> str:
    if title_lines:
        title = " ".join(_normalize_text(line.get("text", "")) for line in title_lines)
        title = title.strip()
        if title:
            return title

    if body_lines:
        first_body_line = _normalize_text(body_lines[0].get("text", ""))
        if first_body_line:
            return first_body_line

    return _normalize_text(page_headline)


def _collect_matched_keywords(text: str, keywords: Iterable[str]) -> list[str]:
    matched: list[str] = []
    for keyword in keywords:
        if keyword_matches_text(text, keyword):
            normalized = _normalize_text(keyword)
            if normalized and normalized not in matched:
                matched.append(normalized)
    return matched


def _crop_article_image(
    screenshot_path: Path,
    entries: list[dict],
    outputs_dir: Path,
    page_number: int,
    article_index: int,
) -> str:
    image = cv2.imread(str(screenshot_path))
    if image is None:
        return f"{SCREENSHOT_BASE_URL}/{screenshot_path.name}"

    rects = [
        _entry_rect(entry)
        for entry in entries
    ]
    rects = [rect for rect in rects if rect is not None]
    if not rects:
        return f"{SCREENSHOT_BASE_URL}/{screenshot_path.name}"

    min_x = max(0, min(rect[0] for rect in rects) - 20)
    min_y = max(0, min(rect[1] for rect in rects) - 20)
    max_x = min(image.shape[1], max(rect[2] for rect in rects) + 20)
    max_y = min(image.shape[0], max(rect[3] for rect in rects) + 20)

    if max_x <= min_x or max_y <= min_y:
        return f"{SCREENSHOT_BASE_URL}/{screenshot_path.name}"

    crop = image[min_y:max_y, min_x:max_x]
    crop_name = f"{screenshot_path.stem}_p{page_number}_article{article_index}.png"
    crop_path = outputs_dir / crop_name
    cv2.imwrite(str(crop_path), crop)
    return f"{OUTPUT_BASE_URL}/{crop_name}"


def _median_height(entries: list[dict]) -> float:
    heights = []
    for entry in entries:
        rect = _entry_rect(entry)
        if rect is None:
            continue
        height = max(0, rect[3] - rect[1])
        if height > 0:
            heights.append(height)
    if not heights:
        return 1.0
    heights.sort()
    middle = len(heights) // 2
    if len(heights) % 2:
        return float(heights[middle])
    return float((heights[middle - 1] + heights[middle]) / 2.0)


def _entry_rect(entry: dict) -> tuple[int, int, int, int] | None:
    rect = entry.get("_rect")
    if rect:
        return tuple(rect)  # type: ignore[return-value]

    bbox = entry.get("bbox")
    if not bbox:
        return None

    xs = [int(point[0]) for point in bbox]
    ys = [int(point[1]) for point in bbox]
    return min(xs), min(ys), max(xs), max(ys)


def _normalize_text(value) -> str:
    return " ".join(str(value).split()).strip()


def _validate_date(date_value: str) -> None:
    try:
        date_cls.fromisoformat(date_value)
    except ValueError as exc:
        raise ValueError("Date must be in YYYY-MM-DD format") from exc
