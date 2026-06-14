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

    def _validate_date(self, date: str, date_format: str = "YYYY-MM-DD") -> bool:
        if date_format == "DD/MM/YYYY":
            try:
                datetime.strptime(date, "%d/%m/%Y")
            except ValueError:
                raise InvalidDateError(
                f"Date '{date}' is not a valid DD/MM/YYYY date"
                )
        elif date_format == "YYYYMMDD":
            if not (len(date) == 8 and date.isdigit() and date.startswith(("202", "203"))):
                raise InvalidDateError(
                f"Date '{date}' is not a valid YYYYMMDD date"
                )
        else:
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
        self._validate_date(date, newspaper_info["date_format"])
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

        # Special handling for Deshonnati Nagpur which includes edition in the date part
        if "deshonnati.com" in newspaper_info["sample_url"]:
            return f"{base_url}DESHONATI_NAGP_{date_str}/page/{page_str}"
        # Ensure base_url ends with / if it doesn't already end with date
        elif not base_url.endswith("/"):
            return f"{base_url}/{date_str}/{page_str}"
        else:
            return f"{base_url}{date_str}/{page_str}"

    def _resolve_query_url(self, newspaper_info: Dict, date: str, page: int) -> str:
        base_url = newspaper_info["sample_url"].split("?")[0]

        # Special handling for Lokshahi Varta newspapers which use 'ced' instead of 'edition'
        if "lokshahivarta.co.in" in newspaper_info["sample_url"]:
            edition = self._extract_ced_from_url(newspaper_info["sample_url"])
            edition_param = edition
            return f"{base_url}?url=home&ced={edition_param}&date={date}&page={page}"
        else:
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

    def _extract_ced_from_url(self, sample_url: str) -> str:
        if "?ced=" in sample_url:
            start = sample_url.find("?ced=") + len("?ced=")
            end = sample_url.find("&", start)
            if end != -1:
                return sample_url[start:end]
            else:
                end = sample_url.find(" ", start)
                if end != -1:
                    return sample_url[start:end]
                else:
                    return sample_url[start:]
        elif "&ced=" in sample_url:
            start = sample_url.find("&ced=") + len("&ced=")
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
            return "16"

    def _extract_base_url_from_sample_url(self, sample_url: str) -> str:
        # Special handling for Deshonnati Nagpur which has pattern /edition/Nagpur/DESHONATI_NAGP/
        if "deshonnati.com" in sample_url:
            # Find the position of DESHONATI_NAGP
            edition_pos = sample_url.find("DESHONATI_NAGP")
            if edition_pos != -1:
                # Find the position of the next "/" after DESHONATI_NAGP
                next_slash_pos = sample_url.find("/", edition_pos + len("DESHONATI_NAGP"))
                if next_slash_pos != -1:
                    # Return base URL with trailing slash for proper URL construction
                    return sample_url[:next_slash_pos] + "/"
        
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
        elif "/edition/" in sample_url:
            # Special handling for Deshonnati Nagpur which has pattern /edition/Nagpur/DESHONATI_NAGP/
            if "deshonnati.com" in sample_url:
                # Find the position of DESHONATI_NAGP
                edition_pos = sample_url.find("DESHONATI_NAGP")
                if edition_pos != -1:
                    # Find the position of the next "/" after DESHONATI_NAGP
                    next_slash_pos = sample_url.find("/", edition_pos + len("DESHONATI_NAGP"))
                    if next_slash_pos != -1:
                        return sample_url[:next_slash_pos]
            # For other newspapers, stop after the edition
            start = sample_url.find("/edition/") + len("/edition/")
            end = sample_url.find("/", start)
            if end != -1:
                return sample_url[:end]
            else:
                return sample_url[start:]
        elif "/nagpur/" in sample_url:
            # Stop before the date (which is the next segment after the edition)
            start = sample_url.find("/nagpur/") + len("/nagpur/")
            end = sample_url.find("/", start)
            if end != -1:
                return sample_url[:end]
            else:
                return sample_url
        else:
            return sample_url

    def get_all_newspapers(self) -> List[str]:
        return [newspaper["name"] for newspaper in self._load_registry()]


registry = NewspaperRegistry()
def resolve_newspaper_url(newspaper: str, date: str, page: int) -> str:
    return registry.resolve_newspaper_url(newspaper, date, page)
