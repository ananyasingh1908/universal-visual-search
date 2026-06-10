import json
from pathlib import Path


def run_ocr(reader, image_path: Path, page_number: int = 1) -> list[dict]:
    results = reader.readtext(str(image_path))
    output = []

    for bbox, text, confidence in results:
        clean_bbox = [
            [int(point[0]), int(point[1])]
            for point in bbox
        ]

        output.append({
            "text": str(text),
            "confidence": float(confidence),
            "bbox": clean_bbox,
            "page_number": page_number,
        })

    return output


def save_ocr_output(document_id: str, ocr_entries: list[dict], data_dir: Path) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    document_path = data_dir / f"{document_id}.json"

    with document_path.open("w", encoding="utf-8") as f:
        json.dump(ocr_entries, f, ensure_ascii=False, indent=2)

    return document_path


def count_words(ocr_entries: list[dict]) -> int:
    return sum(len(entry["text"].split()) for entry in ocr_entries)


def process_image_document(reader, image_path: Path, document_id: str, data_dir: Path) -> dict:
    ocr_entries = run_ocr(reader, image_path)
    save_ocr_output(document_id, ocr_entries, data_dir)

    return {
        "document_id": document_id,
        "words_found": count_words(ocr_entries)
    }
