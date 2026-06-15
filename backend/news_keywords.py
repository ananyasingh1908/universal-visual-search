from __future__ import annotations

from functools import lru_cache
from typing import Iterable


def _normalize_text(value: str) -> str:
    return " ".join(str(value).split()).strip()


def _split_keyword_block(block: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in block.splitlines() if line.strip())


def _unique_keywords(keywords: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []

    for keyword in keywords:
        cleaned = _normalize_text(keyword)
        if not cleaned:
            continue

        normalized = cleaned.casefold()
        if normalized in seen:
            continue

        seen.add(normalized)
        ordered.append(cleaned)

    return tuple(ordered)


class _NewsKeywordCatalog:
    ENGLISH_BLOCK = """
electricity board
state electricity board
electricity department
power distribution company
distribution company
distribution utility
discom
genco
transco

power grid
electric grid
grid substation
substation

transformer
distribution transformer
power transformer

switchyard
feeder

transmission line
distribution line

electric pole
transmission tower

load dispatch centre

smart meter
digital meter
prepaid meter
meter reading
net metering

electricity bill
power bill

electricity connection
new connection
reconnection
disconnection

electrification
rural electrification

power outage
electricity outage
power cut
load shedding
blackout
power failure
grid failure

electricity theft
power theft

electricity tariff
power tariff

HT line
LT line

circuit breaker
switchgear
isolator
relay
busbar

electricity consumer
consumer grievance

transformer failure
transformer replacement
transformer repair

feeder fault
line fault
cable fault

electrocution
electric shock

lineman
junior engineer
assistant engineer
executive engineer
chief engineer

CEA
CERC
SERC
JERC

power station
generation station
thermal power plant
hydroelectric station
"""

    MARATHI_BLOCK = """
वीज
विद्युत

वीज मंडळ
विद्युत मंडळ

महावितरण
महापारेषण
महानिर्मिती

वीज विभाग
विद्युत विभाग

वीज निर्मिती
वीज वितरण
वीज पारेषण
वीज पुरवठा

उपकेंद्र
विद्युत उपकेंद्र

ट्रान्सफॉर्मर
रोहित्र

फीडर
स्विचयार्ड

पारेषण लाईन
वितरण लाईन

वीज वाहिनी

वीज खांब
पारेषण मनोरा

स्मार्ट मीटर
डिजिटल मीटर
प्रीपेड मीटर

मीटर वाचन
मीटर बदल

वीज बिल

वीज ग्राहक

वीज जोडणी
नवीन वीज जोडणी

वीज खंडित
वीज कपात
लोडशेडिंग

ग्रीड बिघाड
वीज बिघाड

वीज चोरी

एचटी लाईन
एलटी लाईन

सर्किट ब्रेकर
स्विचगिअर

व्होल्टेज समस्या

रोहित्र निकामी
रोहित्र जळाले
रोहित्र बदल

फीडर बिघाड

विद्युत अपघात
वीज धक्का

लाईनमन

कनिष्ठ अभियंता
सहाय्यक अभियंता
कार्यकारी अभियंता
मुख्य अभियंता
"""

    HINDI_BLOCK = """
बिजली
विद्युत

बिजली बोर्ड
विद्युत बोर्ड

बिजली विभाग
विद्युत विभाग

बिजली उत्पादन
बिजली वितरण
बिजली पारेषण
बिजली आपूर्ति

उपकेंद्र
विद्युत उपकेंद्र

ट्रांसफार्मर

फीडर
स्विचयार्ड

पारेषण लाइन
वितरण लाइन

बिजली लाइन

बिजली खंभा
ट्रांसमिशन टावर

स्मार्ट मीटर
डिजिटल मीटर
प्रीपेड मीटर

मीटर रीडिंग
मीटर बदल

बिजली बिल

बिजली उपभोक्ता

बिजली कनेक्शन

बिजली कटौती
बिजली गुल
लोड शेडिंग

ग्रिड फेल

बिजली चोरी

एचटी लाइन
एलटी लाइन

सर्किट ब्रेकर
स्विचगियर

वोल्टेज समस्या

ट्रांसफार्मर खराब
ट्रांसफार्मर जला

फीडर खराब

विद्युत दुर्घटना
करंट लगना

लाइनमैन

कनिष्ठ अभियंता
सहायक अभियंता
कार्यकारी अभियंता
मुख्य अभियंता
"""

    @classmethod
    def all_keywords(cls) -> tuple[str, ...]:
        return _unique_keywords(
            _split_keyword_block(cls.ENGLISH_BLOCK)
            + _split_keyword_block(cls.MARATHI_BLOCK)
            + _split_keyword_block(cls.HINDI_BLOCK)
        )


@lru_cache(maxsize=1)
def get_news_keywords() -> tuple[str, ...]:
    return _NewsKeywordCatalog.all_keywords()


def keyword_matches_text(text: str, keyword: str) -> bool:
    normalized_text = _normalize_text(text).casefold()
    normalized_keyword = _normalize_text(keyword).casefold()

    if not normalized_text or not normalized_keyword:
        return False

    if " " in normalized_keyword:
        return normalized_keyword in normalized_text

    import re

    pattern = rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)"
    if re.search(pattern, normalized_text) is not None:
        return True

    compact_text = re.sub(r"[\s\-]+", "", normalized_text)
    compact_keyword = re.sub(r"[\s\-]+", "", normalized_keyword)
    return bool(compact_keyword) and compact_keyword in compact_text


def keyword_matches_any_text(
    text: str,
    keywords: Iterable[str] | None = None,
) -> bool:
    source_keywords = keywords if keywords is not None else get_news_keywords()
    return any(keyword_matches_text(text, keyword) for keyword in source_keywords)


def first_matching_keyword(
    text: str,
    keywords: Iterable[str] | None = None,
) -> str | None:
    source_keywords = keywords if keywords is not None else get_news_keywords()
    for keyword in source_keywords:
        if keyword_matches_text(text, keyword):
            return keyword
    return None
