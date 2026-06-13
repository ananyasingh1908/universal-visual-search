import json
import re
from pathlib import Path

import cv2
from news_keywords import (
    first_matching_keyword,
    keyword_matches_any_text,
)

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


class DocumentNotFoundError(Exception):
    pass


class OriginalImageNotFoundError(Exception):
    pass


class ImageReadError(Exception):
    pass


def _normalize_text(value: str) -> str:
    return " ".join(str(value).split()).strip()


def keyword_matches_text(text: str, keyword: str) -> bool:
    normalized_text = _normalize_text(text).casefold()
    normalized_keyword = _normalize_text(keyword).casefold()

    if not normalized_text or not normalized_keyword:
        return False

    if " " in normalized_keyword:
        return normalized_keyword in normalized_text

    pattern = rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)"
    if re.search(pattern, normalized_text) is not None:
        return True

    compact_text = re.sub(r"[\s\-]+", "", normalized_text)
    compact_keyword = re.sub(r"[\s\-]+", "", normalized_keyword)
    return bool(compact_keyword) and compact_keyword in compact_text


def highlight_keyword(
    document_id: str,
    keyword: str,
    base_dir: Path,
    page_number: int | None = None,
) -> dict:
    return highlight_keywords(
        document_id,
        [keyword],
        base_dir,
        page_number=page_number,
    )


def highlight_keywords(
    document_id: str,
    keywords: list[str],
    base_dir: Path,
    page_number: int | None = None,
) -> dict:
    data_dir = base_dir / "data"
    outputs_dir = base_dir / "outputs"

    document_path = data_dir / f"{document_id}.json"
    if not document_path.is_file():
        raise DocumentNotFoundError("Document not found")

    with document_path.open("r", encoding="utf-8") as f:
        ocr_entries = json.load(f)

    all_matches = [
        entry
        for entry in ocr_entries
        if keyword_matches_any_text(str(entry.get("text", "")), keywords)
    ]

    if not all_matches:
        return {
            "highlighted_image_url": None,
            "total_matches": 0,
            "page_number": page_number,
        }

    target_page = page_number
    if target_page is None:
        target_page = all_matches[0].get("page_number", 1)

    page_matches = [
        m for m in all_matches
        if m.get("page_number", 1) == target_page
    ]
    if not page_matches:
        page_matches = all_matches

    image_path = _find_original_image(document_id, base_dir, target_page)
    if image_path is None:
        raise OriginalImageNotFoundError(
            f"Original image not found for page {target_page}"
        )

    image = cv2.imread(str(image_path))
    if image is None:
        raise ImageReadError("Original image could not be read")

    for entry in page_matches:
        _draw_bbox(image, entry.get("bbox", []))

    outputs_dir.mkdir(parents=True, exist_ok=True)
    page_suffix = (
        f"_p{target_page}"
        if target_page != 1 or _has_page_numbered_screenshots(document_id, base_dir)
        else ""
    )
    matched_keyword = first_matching_keyword(
        str(page_matches[0].get("text", "")),
        keywords,
    ) or "keywords"
    output_name = f"{document_id}{page_suffix}_{_safe_filename_part(matched_keyword)}.png"
    output_path = outputs_dir / output_name
    cv2.imwrite(str(output_path), image)

    return {
        "highlighted_image_url": f"http://127.0.0.1:8000/outputs/{output_path.name}",
        "total_matches": len(page_matches),
        "page_number": target_page,
        "matched_keyword": matched_keyword,
    }


def _has_page_numbered_screenshots(document_id: str, base_dir: Path) -> bool:
    screenshots_dir = base_dir / "screenshots"
    if not screenshots_dir.is_dir():
        return False
    return any(
        screenshots_dir.glob(f"{document_id}_p*.png")
    )


def _find_original_image(
    document_id: str,
    base_dir: Path,
    page_number: int | None = None,
) -> Path | None:
    search_dirs = [
        base_dir / "uploads",
        base_dir / "screenshots",
    ]

    for image_dir in search_dirs:
        if page_number is not None:
            for ext in IMAGE_EXTENSIONS:
                page_path = image_dir / f"{document_id}_p{page_number}{ext}"
                if page_path.is_file():
                    return page_path

        image_path = _find_image_in_directory(image_dir, document_id)
        if image_path is not None:
            return image_path

    return None


def _find_image_in_directory(image_dir: Path, document_id: str) -> Path | None:
    if not image_dir.is_dir():
        return None

    for extension in IMAGE_EXTENSIONS:
        image_path = image_dir / f"{document_id}{extension}"
        if image_path.is_file():
            return image_path

    return None


def _draw_bbox(image, bbox: list) -> None:
    if not bbox:
        return

    xs = [int(point[0]) for point in bbox]
    ys = [int(point[1]) for point in bbox]
    top_left = (min(xs), min(ys))
    bottom_right = (max(xs), max(ys))

    cv2.rectangle(image, top_left, bottom_right, (0, 255, 255), 2)


def _safe_filename_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return cleaned.strip("._") or "keyword"
