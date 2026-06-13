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
electricity
electrical
power generation
power transmission
power distribution
power supply
power plant
power station
grid
power grid
national grid
smart grid
electric grid
grid station
grid substation
substation
switchyard
transformer
feeder
distribution transformer
power transformer
transmission line
distribution line
power line
electric pole
transmission tower
load dispatch
load dispatch centre
load shedding
electricity board
state electricity board
central electricity authority
CEA
central electricity regulatory commission
CERC
state electricity regulatory commission
SERC
joint electricity regulatory commission
JERC
electricity regulatory commission
electricity department
discom
distribution company
distribution utility
genco
generation company
transco
transmission company
electric utility
electricity company
electricity network
transmission network
distribution network
generation station
generating station
thermal power
thermal power plant
thermal station
coal power plant
coal based power plant
hydro power
hydroelectric power
hydel project
hydroelectric station
dam
reservoir
pumped storage
solar power
solar energy
solar plant
solar project
solar park
floating solar
rooftop solar
wind power
wind energy
wind farm
renewable energy
smart meter
digital meter
prepaid meter
meter reading
net metering
electricity bill
connection
new connection
disconnection
reconnection
electrification
rural electrification
village electrification
power outage
electricity outage
power cut
grid failure
power failure
supply disruption
maintenance shutdown
planned shutdown
electricity theft
power theft
renewable purchase obligation
RPO
electricity act
high voltage
extra high voltage
ultra high voltage
HT line
LT line
EHV line
UHV line
11 kV
22 kV
33 kV
66 kV
110 kV
132 kV
220 kV
400 kV
765 kV
800 kV
HVDC
HVAC
reactor
capacitor bank
busbar
relay
circuit breaker
isolator
switchgear
"""

    MARATHI_BLOCK = """
वीज
विद्युत
वीज मंडळ
विद्युत मंडळ
राज्य वीज मंडळ
केंद्रीय वीज प्राधिकरण
केंद्रीय विद्युत प्राधिकरण
वीज विभाग
विद्युत विभाग
वीज कंपनी
विद्युत कंपनी
वीज निर्मिती
विद्युत निर्मिती
वीज उत्पादन
विद्युत उत्पादन
वीज वितरण
विद्युत वितरण
वीज पारेषण
विद्युत पारेषण
वीज पुरवठा
विद्युत पुरवठा
वीज प्रकल्प
विद्युत प्रकल्प
वीज केंद्र
वीज स्टेशन
वीज ग्रीड
राष्ट्रीय ग्रीड
स्मार्ट ग्रीड
लोड डिस्पॅच केंद्र
उपकेंद्र
विद्युत उपकेंद्र
ट्रान्सफॉर्मर
विद्युत रोहित्र
फीडर
स्विचयार्ड
वीज वाहिनी
पारेषण लाईन
वितरण लाईन
वीज खांब
पारेषण मनोरा
स्मार्ट मीटर
डिजिटल मीटर
प्रीपेड मीटर
नेट मीटरिंग
मीटर वाचन
मीटर बदल
मीटर बसविणे
वीज बिल
वीज ग्राहक
वीज जोडणी
नवीन वीज जोडणी
वीज खंडित
वीज पुरवठा बंद
वीज कपात
लोडशेडिंग
ग्रीड बिघाड
वीज बिघाड
वीज चोरी
नवीकरणीय ऊर्जा
सौर ऊर्जा
सौर वीज
सौर प्रकल्प
सौर पार्क
रूफटॉप सोलर
पवन ऊर्जा
जलविद्युत
जलविद्युत प्रकल्प
धरण
जलाशय
pumped storage
पंप्ड स्टोरेज
औष्णिक विद्युत
औष्णिक प्रकल्प
कोळसा आधारित प्रकल्प
तापीय वीज प्रकल्प
बॉयलर
टर्बाइन
महाराष्ट्र राज्य वीज मंडळ
महावितरण
महापारेषण
महानिर्मिती
महाराष्ट्र विद्युत नियामक आयोग
"""

    HINDI_BLOCK = """
बिजली
विद्युत
बिजली बोर्ड
विद्युत बोर्ड
राज्य विद्युत बोर्ड
केंद्रीय विद्युत प्राधिकरण
बिजली विभाग
विद्युत विभाग
बिजली कंपनी
विद्युत कंपनी
बिजली उत्पादन
विद्युत उत्पादन
बिजली वितरण
विद्युत वितरण
बिजली पारेषण
विद्युत पारेषण
बिजली आपूर्ति
विद्युत आपूर्ति
बिजली परियोजना
विद्युत परियोजना
बिजली संयंत्र
विद्युत संयंत्र
पावर स्टेशन
बिजली स्टेशन
ग्रिड
राष्ट्रीय ग्रिड
स्मार्ट ग्रिड
लोड डिस्पैच केंद्र
उपकेंद्र
विद्युत उपकेंद्र
ट्रांसफार्मर
फीडर
स्विचयार्ड
बिजली लाइन
पारेषण लाइन
वितरण लाइन
बिजली खंभा
ट्रांसमिशन टावर
स्मार्ट मीटर
डिजिटल मीटर
प्रीपेड मीटर
नेट मीटरिंग
मीटर रीडिंग
मीटर बदल
मीटर स्थापना
बिजली बिल
बिजली उपभोक्ता
बिजली कनेक्शन
नया कनेक्शन
बिजली कटौती
बिजली गुल
लोड शेडिंग
ग्रिड फेल
बिजली बाधित
बिजली चोरी
नवीकरणीय ऊर्जा
सौर ऊर्जा
सौर बिजली
सौर परियोजना
सौर पार्क
रूफटॉप सोलर
पवन ऊर्जा
जल विद्युत
जलविद्युत परियोजना
बांध
जलाशय
पंप्ड स्टोरेज
ताप विद्युत
थर्मल पावर
कोयला आधारित संयंत्र
तापीय बिजलीघर
बॉयलर
टर्बाइन
महाराष्ट्र राज्य विद्युत मंडल
महावितरण
महापारेषण
महानिर्मिती
महाराष्ट्र विद्युत नियामक आयोग
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
