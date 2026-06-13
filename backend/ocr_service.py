import base64
import json
import os
from functools import lru_cache
from pathlib import Path
from statistics import median
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import logging
import cv2
import numpy as np

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

LOCAL_ENV_PATH = Path(__file__).resolve().parent / ".env"
VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"

# Configure module logger
logger = logging.getLogger("ocr_service")

# Load .env via python-dotenv if available, otherwise fall back to simple loader
if load_dotenv is not None:
    try:
        load_dotenv(LOCAL_ENV_PATH)
        logger.debug("Loaded .env via python-dotenv: %s", LOCAL_ENV_PATH)
    except Exception:
        logger.exception("Failed to load .env using python-dotenv")
else:
    # minimal fallback: only set vars that are not already in the environment
    if LOCAL_ENV_PATH.is_file():
        try:
            with LOCAL_ENV_PATH.open("r", encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue

                    key, value = line.split("=", 1)
                    key = key.strip()
                    if not key or key in os.environ:
                        continue

                    os.environ[key] = value.strip().strip('"').strip("'")
            logger.debug("Loaded .env via fallback loader: %s", LOCAL_ENV_PATH)
        except Exception:
            logger.exception("Failed to load .env fallback loader")


def run_ocr(reader, image_path: Path, page_number: int = 1) -> list[dict]:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    vision_api_key = _get_google_vision_api_key()
    using_vision = bool(vision_api_key)
    logger.info("run_ocr: image=%s page=%s using_google_vision=%s", image_path, page_number, using_vision)

    try:
        if using_vision:
            detections = _collect_google_vision_detections(
                image_path, page_number, vision_api_key
            )
        else:
            detections = _collect_easyocr_detections(reader, image, page_number)
    except Exception:
        logger.exception("OCR backend failed for image=%s", image_path)
        raise

    merged = _merge_detections(detections)
    _mark_headlines(merged, image.shape)
    finalized = _finalize_entries(merged)
    try:
        all_text = " ".join(entry.get("text", "") for entry in finalized)
        logger.info("OCR result entries=%d total_text_length=%d", len(finalized), len(all_text))
        logger.debug("OCR preview: %s", (all_text or "")[:200])
    except Exception:
        logger.exception("Failed to log OCR text preview")
    return finalized


def save_ocr_output(document_id: str, ocr_entries: list[dict], data_dir: Path) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    document_path = data_dir / f"{document_id}.json"

    with document_path.open("w", encoding="utf-8") as f:
        json.dump(ocr_entries, f, ensure_ascii=False, indent=2)

    return document_path


def count_words(ocr_entries: list[dict]) -> int:
    return sum(len(entry["text"].split()) for entry in ocr_entries)


def summarize_headline(ocr_entries: list[dict]) -> dict:
    headline_entries = [
        entry for entry in ocr_entries if entry.get("is_headline")
    ]
    if not headline_entries:
        return {
            "headline_text": "",
            "headline_lines": [],
        }

    lines = _group_entries_into_lines(
        headline_entries,
        max(1.0, _median_height(headline_entries)),
    )
    headline_lines = [
        " ".join(entry["text"] for entry in line["entries"]).strip()
        for line in sorted(lines, key=lambda item: item["top"])
    ]
    headline_lines = [line for line in headline_lines if line]

    return {
        "headline_text": " ".join(headline_lines).strip(),
        "headline_lines": headline_lines,
    }


def process_image_document(reader, image_path: Path, document_id: str, data_dir: Path) -> dict:
    ocr_entries = run_ocr(reader, image_path)
    save_ocr_output(document_id, ocr_entries, data_dir)
    headline = summarize_headline(ocr_entries)

    return {
        "document_id": document_id,
        "words_found": count_words(ocr_entries),
        "headline_text": headline["headline_text"],
        "headline_lines": headline["headline_lines"],
    }


def _get_google_vision_api_key() -> str:
    return os.getenv("GOOGLE_CLOUD_VISION_API_KEY", "").strip()
    print("API KEY FOUND:", bool(os.getenv("GOOGLE_CLOUD_VISION_API_KEY")))

@lru_cache(maxsize=1)
def _get_easyocr_reader():
    import easyocr

    return easyocr.Reader(["en"])


def _collect_easyocr_detections(reader, image, page_number: int) -> list[dict]:
    detections: list[dict] = []
    ocr_reader = reader or _get_easyocr_reader()
    logger.warning("Using EasyOCR fallback for OCR (Google Vision key not present or failed)")

    for variant_name, variant_image, settings in _build_image_variants(image):
        try:
            results = ocr_reader.readtext(
                variant_image,
                detail=1,
                paragraph=False,
                decoder="beamsearch",
                batch_size=1,
                canvas_size=settings["canvas_size"],
                mag_ratio=settings["mag_ratio"],
                text_threshold=settings["text_threshold"],
                low_text=settings["low_text"],
                link_threshold=settings["link_threshold"],
                contrast_ths=0.05,
                adjust_contrast=0.7,
                min_size=settings["min_size"],
            )
        except Exception:
            continue

        for bbox, text, confidence in results:
            normalized_text = _normalize_text(text)
            if not normalized_text:
                continue

            rect = _bbox_to_rect(bbox)
            if rect is None:
                continue

            detections.append({
                "text": normalized_text,
                "confidence": float(confidence),
                "bbox": _normalize_bbox(bbox),
                "page_number": page_number,
                "_rect": rect,
                "_variant": variant_name,
            })

    return detections


def _collect_google_vision_detections(
    image_path: Path,
    page_number: int,
    api_key: str,
) -> list[dict]:
    image_bytes = image_path.read_bytes()
    response = _call_google_vision_api(image_bytes, api_key)
    detections = _extract_google_vision_detections(response, page_number)

    if detections:
        return detections

    return _extract_vision_text_annotations(response, page_number)


def _call_google_vision_api(image_bytes: bytes, api_key: str) -> dict:
    payload = {
        "requests": [
            {
                "image": {
                    "content": base64.b64encode(image_bytes).decode("ascii"),
                },
                "features": [
                    {
                        "type": "DOCUMENT_TEXT_DETECTION",
                    }
                ],
            }
        ]
    }

    request = Request(
        f"{VISION_API_URL}?key={api_key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    logger.debug("Calling Google Vision API; payload_size=%d bytes", len(image_bytes))
    try:
        with urlopen(request, timeout=60) as response:
            raw = response.read()
            response_payload = json.loads(raw.decode("utf-8"))
            try:
                ft = response_payload.get("responses", [{}])[0].get("fullTextAnnotation", {}).get("text", "")
                logger.info("Google Vision returned text length=%d", len(ft))
                logger.debug("Google Vision first 200 chars: %s", (ft or '')[:200])
            except Exception:
                logger.debug("Could not parse fullTextAnnotation for logging")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Google Vision API request failed ({exc.code}): {detail}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            f"Google Vision API request failed: {exc.reason}"
        ) from exc

    responses = response_payload.get("responses") or []
    if not responses:
        return {}

    error = responses[0].get("error")
    if error:
        message = error.get("message", "Unknown Google Vision error")
        raise RuntimeError(message)

    return responses[0]


def _extract_google_vision_detections(
    response: dict,
    page_number: int,
) -> list[dict]:
    detections: list[dict] = []
    full_text = response.get("fullTextAnnotation") or {}

    for page in full_text.get("pages", []):
        for block in page.get("blocks", []):
            for paragraph in block.get("paragraphs", []):
                detection = _paragraph_to_detection(paragraph, page_number)
                if detection is not None:
                    detections.append(detection)

    return detections


def _extract_vision_text_annotations(
    response: dict,
    page_number: int,
) -> list[dict]:
    detections: list[dict] = []
    annotations = response.get("textAnnotations") or []

    for annotation in annotations[1:] or annotations[:1]:
        text = _normalize_text(annotation.get("description"))
        bbox = _normalize_bbox_from_vertices(
            (annotation.get("boundingPoly") or {}).get("vertices") or []
        )
        rect = _bbox_to_rect(bbox)
        if not text or rect is None:
            continue

        detections.append({
            "text": text,
            "confidence": 0.0,
            "bbox": bbox,
            "page_number": page_number,
            "_rect": rect,
        })

    return detections


def _paragraph_to_detection(paragraph: dict, page_number: int) -> dict | None:
    words = paragraph.get("words") or []
    text_parts = []
    confidences = []

    for word in words:
        word_text = _vision_word_text(word)
        if word_text:
            text_parts.append(word_text)

        confidence = word.get("confidence")
        if confidence is not None:
            confidences.append(float(confidence))

    text = _normalize_text(" ".join(text_parts))
    bbox = _normalize_bbox_from_vertices(
        (paragraph.get("boundingBox") or {}).get("vertices") or []
    )
    rect = _bbox_to_rect(bbox)
    if not text or rect is None:
        return None

    confidence = float(paragraph.get("confidence") or 0.0)
    if confidence == 0.0 and confidences:
        confidence = sum(confidences) / len(confidences)

    return {
        "text": text,
        "confidence": confidence,
        "bbox": bbox,
        "page_number": page_number,
        "_rect": rect,
    }


def _vision_word_text(word: dict) -> str:
    symbols = word.get("symbols") or []
    if symbols:
        return _normalize_text(
            "".join(str(symbol.get("text", "")) for symbol in symbols)
        )

    return _normalize_text(word.get("text") or word.get("description") or "")


def _build_image_variants(image):
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(grayscale)
    denoised = cv2.bilateralFilter(clahe, 9, 75, 75)

    upscaled = cv2.resize(
        denoised,
        None,
        fx=2.0,
        fy=2.0,
        interpolation=cv2.INTER_CUBIC,
    )

    sharpen_kernel = np.array(
        [
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0],
        ],
        dtype=np.float32,
    )
    sharpened = cv2.filter2D(upscaled, -1, sharpen_kernel)
    thresholded = cv2.adaptiveThreshold(
        sharpened,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    return [
        (
            "original",
            image,
            {
                "canvas_size": 3200,
                "mag_ratio": 1.5,
                "text_threshold": 0.55,
                "low_text": 0.3,
                "link_threshold": 0.4,
                "min_size": 6,
            },
        ),
        (
            "headline_focus",
            image[: max(int(image.shape[0] * 0.4), 1), :],
            {
                "canvas_size": 3840,
                "mag_ratio": 2.4,
                "text_threshold": 0.45,
                "low_text": 0.2,
                "link_threshold": 0.3,
                "min_size": 5,
            },
        ),
        (
            "enhanced",
            cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR),
            {
                "canvas_size": 3840,
                "mag_ratio": 2.0,
                "text_threshold": 0.5,
                "low_text": 0.25,
                "link_threshold": 0.35,
                "min_size": 6,
            },
        ),
        (
            "thresholded",
            cv2.cvtColor(thresholded, cv2.COLOR_GRAY2BGR),
            {
                "canvas_size": 3840,
                "mag_ratio": 2.0,
                "text_threshold": 0.45,
                "low_text": 0.2,
                "link_threshold": 0.3,
                "min_size": 5,
            },
        ),
    ]


def _merge_detections(detections: list[dict]) -> list[dict]:
    merged: list[dict] = []

    for detection in sorted(
        detections,
        key=lambda item: (item["confidence"], _rect_area(item["_rect"])),
        reverse=True,
    ):
        if any(_boxes_match(detection["_rect"], kept["_rect"]) for kept in merged):
            continue
        merged.append(detection)

    return merged


def _mark_headlines(entries: list[dict], image_shape) -> None:
    for entry in entries:
        entry["is_headline"] = False

    if not entries:
        return

    page_height, page_width = image_shape[:2]
    heights = [
        _rect_height(rect)
        for entry in entries
        if (rect := _entry_rect(entry)) is not None and _rect_height(rect) > 0
    ]
    widths = [
        _rect_width(rect)
        for entry in entries
        if (rect := _entry_rect(entry)) is not None and _rect_width(rect) > 0
    ]
    if not heights or not widths:
        return

    median_height = max(1.0, float(median(heights)))
    top_band = max(int(page_height * 0.32), int(median_height * 6))

    top_entries = [
        entry
        for entry in entries
        if (rect := _entry_rect(entry)) is not None and rect[1] <= top_band
    ]
    if not top_entries:
        return

    candidate_lines = _group_entries_into_lines(top_entries, median_height)
    scored_lines = []
    for line in candidate_lines:
        avg_height = line["avg_height"]
        if avg_height < max(median_height * 1.15, 12):
            continue

        score = (
            (avg_height / median_height) * 0.45
            + (1.0 - min(line["top"] / max(page_height, 1), 1.0)) * 0.25
            + line["avg_confidence"] * 0.2
            + min(line["width"] / max(page_width, 1), 1.0) * 0.1
        )
        scored_lines.append({
            **line,
            "score": score,
        })

    if not scored_lines:
        return

    scored_lines.sort(key=lambda item: item["top"])
    best_line = max(scored_lines, key=lambda item: item["score"])
    headline_lines = [best_line]

    for line in scored_lines:
        if line is best_line:
            continue

        close_to_best = line["top"] <= best_line["bottom"] + max(median_height * 1.2, 24)
        similar_scale = line["avg_height"] >= best_line["avg_height"] * 0.7
        strong_enough = line["score"] >= best_line["score"] * 0.7

        if close_to_best and similar_scale and strong_enough:
            headline_lines.append(line)

    headline_entries = {
        id(entry)
        for line in headline_lines
        for entry in line["entries"]
    }

    for entry in entries:
        if id(entry) in headline_entries:
            entry["is_headline"] = True


def _group_entries_into_lines(entries: list[dict], median_height: float) -> list[dict]:
    if not entries:
        return []

    tolerance = max(12.0, median_height * 0.8)
    clusters: list[dict] = []

    for entry in entries:
        rect = _entry_rect(entry)
        if rect is None:
            continue

        x1, y1, x2, y2 = rect
        center_y = (y1 + y2) / 2.0
        placed = False

        for cluster in clusters:
            if abs(center_y - cluster["center_y"]) <= tolerance:
                previous_count = len(cluster["entries"])
                cluster["entries"].append(entry)
                cluster["center_y"] = (
                    (cluster["center_y"] * previous_count) + center_y
                ) / (previous_count + 1)
                cluster["top"] = min(cluster["top"], y1)
                cluster["bottom"] = max(cluster["bottom"], y2)
                cluster["left"] = min(cluster["left"], x1)
                cluster["right"] = max(cluster["right"], x2)
                cluster["heights"].append(y2 - y1)
                cluster["confidences"].append(entry["confidence"])
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
                "heights": [y2 - y1],
                "confidences": [entry["confidence"]],
            })

    grouped = []
    for cluster in clusters:
        entries_sorted = sorted(
            cluster["entries"],
            key=lambda item: (_entry_rect(item) or (0, 0, 0, 0))[0],
        )
        grouped.append({
            "entries": entries_sorted,
            "top": cluster["top"],
            "bottom": cluster["bottom"],
            "left": cluster["left"],
            "right": cluster["right"],
            "width": cluster["right"] - cluster["left"],
            "avg_height": sum(cluster["heights"]) / max(len(cluster["heights"]), 1),
            "avg_confidence": sum(cluster["confidences"]) / max(len(cluster["confidences"]), 1),
        })

    return grouped


def _finalize_entries(entries: list[dict]) -> list[dict]:
    finalized = []

    for entry in sorted(
        entries,
        key=lambda item: (
            item.get("page_number", 1),
            item["_rect"][1],
            item["_rect"][0],
            -item["confidence"],
        ),
    ):
        finalized.append({
            key: value
            for key, value in entry.items()
            if not key.startswith("_")
        })

    return finalized


def _normalize_text(value) -> str:
    return " ".join(str(value).split()).strip()


def _normalize_bbox(bbox) -> list[list[int]]:
    return [
        [int(point[0]), int(point[1])]
        for point in bbox
    ]


def _normalize_bbox_from_vertices(vertices) -> list[list[int]]:
    normalized: list[list[int]] = []

    for point in vertices:
        if isinstance(point, dict):
            x = point.get("x", 0) or 0
            y = point.get("y", 0) or 0
        else:
            x = 0
            y = 0

        normalized.append([int(x), int(y)])

    return normalized


def _bbox_to_rect(bbox) -> tuple[int, int, int, int] | None:
    if not bbox:
        return None

    xs = [int(point[0]) for point in bbox]
    ys = [int(point[1]) for point in bbox]
    return min(xs), min(ys), max(xs), max(ys)


def _rect_width(rect: tuple[int, int, int, int]) -> int:
    return max(0, rect[2] - rect[0])


def _rect_height(rect: tuple[int, int, int, int]) -> int:
    return max(0, rect[3] - rect[1])


def _rect_area(rect: tuple[int, int, int, int]) -> int:
    return _rect_width(rect) * _rect_height(rect)


def _intersection_area(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
) -> int:
    x_left = max(left[0], right[0])
    y_top = max(left[1], right[1])
    x_right = min(left[2], right[2])
    y_bottom = min(left[3], right[3])

    if x_right <= x_left or y_bottom <= y_top:
        return 0

    return (x_right - x_left) * (y_bottom - y_top)


def _rect_iou(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
) -> float:
    intersection = _intersection_area(left, right)
    if intersection == 0:
        return 0.0

    union = _rect_area(left) + _rect_area(right) - intersection
    if union <= 0:
        return 0.0

    return intersection / union


def _boxes_match(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
) -> bool:
    if _rect_iou(left, right) >= 0.45:
        return True

    intersection = _intersection_area(left, right)
    if intersection == 0:
        return False

    smaller_area = max(1, min(_rect_area(left), _rect_area(right)))
    return (intersection / smaller_area) >= 0.65


def _median_height(entries: list[dict]) -> float:
    heights = [
        _rect_height(rect)
        for entry in entries
        if (rect := _entry_rect(entry)) is not None and _rect_height(rect) > 0
    ]
    if not heights:
        return 1.0
    return float(median(heights))


def _entry_rect(entry: dict) -> tuple[int, int, int, int] | None:
    rect = entry.get("_rect")
    if rect is not None:
        return rect

    bbox = entry.get("bbox")
    if not bbox:
        return None

    return _bbox_to_rect(bbox)
