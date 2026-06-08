import json
import re
from pathlib import Path

import cv2

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


class DocumentNotFoundError(Exception):
    pass


class OriginalImageNotFoundError(Exception):
    pass


class ImageReadError(Exception):
    pass


def highlight_keyword(document_id: str, keyword: str, base_dir: Path) -> dict:
    data_dir = base_dir / "data"
    outputs_dir = base_dir / "outputs"

    document_path = data_dir / f"{document_id}.json"
    if not document_path.is_file():
        raise DocumentNotFoundError("Document not found")

    image_path = _find_original_image(document_id, base_dir)
    if image_path is None:
        raise OriginalImageNotFoundError("Original image not found")

    with document_path.open("r", encoding="utf-8") as f:
        ocr_entries = json.load(f)

    keyword_lower = keyword.lower()
    matches = [
        entry
        for entry in ocr_entries
        if keyword_lower in str(entry.get("text", "")).lower()
    ]

    image = cv2.imread(str(image_path))
    if image is None:
        raise ImageReadError("Original image could not be read")

    for entry in matches:
        _draw_bbox(image, entry.get("bbox", []))

    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_name = f"{document_id}_{_safe_filename_part(keyword)}.png"
    output_path = outputs_dir / output_name
    cv2.imwrite(str(output_path), image)

    filename = output_path.name

    return {
        "highlighted_image_url": f"http://127.0.0.1:8000/outputs/{filename}",
        "total_matches": len(matches),
    }


def _find_original_image(document_id: str, base_dir: Path) -> Path | None:
    search_dirs = [
        base_dir / "uploads",
        base_dir / "screenshots",
    ]

    for image_dir in search_dirs:
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
