import json
import re
from pathlib import Path
from typing import Dict, List
from urllib.parse import quote
from datetime import datetime


class NewspaperNotFoundError(Exception):
    pass
class InvalidDateError(Exception):
    pass
class InvalidPageError(Exception):
    pass
class NewspaperRegistry:
    def __init__(self, registry_path: str = "backend/newspaper_registry.json"):
        import os
        BASE_DIR = Path(__file__).resolve().parent
        print(f"NewspaperRegistry: __file__ = {__file__}")
        print(f"NewspaperRegistry: BASE_DIR = {BASE_DIR}")
        
        if registry_path == "backend/newspaper_registry.json":
            self.registry_path = BASE_DIR / "newspaper_registry.json"
            print(f"NewspaperRegistry: Using absolute path: {self.registry_path}")
        else:
            self.registry_path = Path(registry_path)
            print(f"NewspaperRegistry: Using custom path: {self.registry_path}")
            
        print(f"NewspaperRegistry: File exists = {os.path.exists(self.registry_path)}")
        self._registry = None

    def _load_registry(self):
        print("=== REGISTRY DEBUG ===")
        print("Path:", self.registry_path)
        print("Exists:", self.registry_path.exists())

        if self._registry is None:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                self._registry = json.load(f)

        return self._registry

    def _find_newspaper_by_name(self, name: str) -> Dict:
        registry = self._load_registry()
        for newspaper in registry:
            if newspaper["name"] == name:
                return newspaper
        raise NewspaperNotFoundError(f"Newspaper '{name}' not found in registry")

    from datetime import datetime

    def _validate_date(self, date: str) -> bool:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise InvalidDateError(
            f"Date '{date}' is not a valid YYYY-MM-DD date"
        )
        return True

    def _validate_page(self, page: int) -> bool:
        if page < 1:
            raise InvalidPageError(f"Page number must be >= 1, got {page}")
        return True

    def resolve_newspaper_url(self, newspaper: str, date: str, page: int) -> str:
        newspaper_info = self._find_newspaper_by_name(newspaper)
        self._validate_date(date)
        self._validate_page(page)

        url_type = newspaper_info["url_type"]

        if url_type == "path":
            return self._resolve_path_url(newspaper_info, date, page)
        elif url_type == "query":
            return self._resolve_query_url(newspaper_info, date, page)
        else:
            raise ValueError(f"Unknown URL type: {url_type}")

    def _resolve_path_url(self, newspaper_info: Dict, date: str, page: int) -> str:
        base_url = self._extract_base_url_from_sample_url(newspaper_info["sample_url"])

        date_str = date
        page_str = str(page)

        # Ensure base_url ends with / if it doesn't already end with date
        if not base_url.endswith("/"):
            return f"{base_url}/{date_str}/{page_str}"
        else:
            return f"{base_url}{date_str}/{page_str}"

    def _resolve_query_url(self, newspaper_info: Dict, date: str, page: int) -> str:
        base_url = newspaper_info["sample_url"].split("?")[0]

        edition = self._extract_edition_from_url(newspaper_info["sample_url"])
        edition_param = quote(edition)
        date_str = date
        page_str = str(page)

        return f"{base_url}?edition={edition_param}&date={date_str}&page={page_str}"

    def _extract_edition_from_base_url(self, sample_url: str) -> str:
        if "/sub-editions/" in sample_url:
            start = sample_url.find("/sub-editions/") + len("/sub-editions/")
            end = sample_url.find("/", start)
            if end != -1:
                return sample_url[start:end]
            else:
                return sample_url[start:]
        elif "/main-editions/" in sample_url:
            start = sample_url.find("/main-editions/") + len("/main-editions/")
            end = sample_url.find("/", start)
            if end != -1:
                return sample_url[start:end]
            else:
                return sample_url[start:]
        elif "/lokmatsamachar/sub-editions/" in sample_url:
            start = sample_url.find("/lokmatsamachar/sub-editions/") + len("/lokmatsamachar/sub-editions/")
            end = sample_url.find("/", start)
            if end != -1:
                return sample_url[start:end]
            else:
                return sample_url[start:]
        elif "?edition=" in sample_url:
            start = sample_url.find("?edition=") + len("?edition=")
            end = sample_url.find("&", start)
            if end != -1:
                return sample_url[start:end]
            else:
                end = sample_url.find("&", start)
                if end == -1:
                    end = sample_url.find("?", start)
                if end != -1:
                    return sample_url[start:end]
                else:
                    return sample_url[start:]
        else:
            return "default"

    def _extract_edition_from_url(self, sample_url: str) -> str:
        if "?edition=" in sample_url:
            start = sample_url.find("?edition=") + len("?edition=")
            end = sample_url.find("&", start)
            if end != -1:
                return sample_url[start:end]
            else:
                end = sample_url.find(" ", start)
                if end != -1:
                    return sample_url[start:end]
                else:
                    return sample_url[start:]
        else:
            return "default"

    def _extract_base_url_from_sample_url(self, sample_url: str) -> str:
        if "/sub-editions/" in sample_url:
            end_date_pos = sample_url.find("/", sample_url.find("/sub-editions/") + len("/sub-editions/"))
            if end_date_pos != -1:
                return sample_url[:end_date_pos]
            else:
                return sample_url
        elif "/main-editions/" in sample_url:
            end_date_pos = sample_url.find("/", sample_url.find("/main-editions/") + len("/main-editions/"))
            if end_date_pos != -1:
                return sample_url[:end_date_pos]
            else:
                return sample_url
        elif "/lokmatsamachar/sub-editions/" in sample_url:
            end_date_pos = sample_url.find("/", sample_url.find("/lokmatsamachar/sub-editions/") + len("/lokmatsamachar/sub-editions/"))
            if end_date_pos != -1:
                return sample_url[:end_date_pos]
            else:
                return sample_url
        elif "?edition=" in sample_url:
            return sample_url.split("?")[0]
        else:
            return sample_url

    def get_all_newspapers(self) -> List[str]:
        return [newspaper["name"] for newspaper in self._load_registry()]


registry = NewspaperRegistry()
def resolve_newspaper_url(newspaper: str, date: str, page: int) -> str:
    return registry.resolve_newspaper_url(newspaper, date, page)
