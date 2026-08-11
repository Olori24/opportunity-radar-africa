from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import Request, urlopen


class _AfDBProcurementParser(HTMLParser):
    """Extract procurement listing links and visible text from AfDB."""

    def __init__(self):
        super().__init__()
        self.items = []
        self._current_href = None
        self._current_text = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if tag == "a" and self._skip_depth == 0:
            attributes = dict(attrs)
            href = attributes.get("href")
            if href:
                self._current_href = href
                self._current_text = []

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag == "a" and self._current_href is not None:
            text = " ".join(" ".join(self._current_text).split())
            if text:
                self.items.append((self._current_href, text))
            self._current_href = None
            self._current_text = []

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._current_href is not None:
            value = " ".join(data.split())
            if value:
                self._current_text.append(value)


class OpportunityAfDBSource:
    """Read live African Development Bank procurement opportunities."""

    SOURCE_ID = "afdb-procurement"
    SOURCE_URL = "https://www.afdb.org/en/projects-and-operations/procurement"
    BASE_URL = "https://www.afdb.org"

    NOTICE_PREFIXES = (
        "eoi -",
        "ami -",
        "gpn -",
        "agpm -",
        "aao -",
        "ppm -",
    )

    COUNTRY_ALIASES = {
        "nigeria": ("nigeria",),
        "ghana": ("ghana",),
        "kenya": ("kenya",),
        "south africa": ("south africa",),
        "egypt": ("egypt",),
        "ethiopia": ("ethiopia",),
        "rwanda": ("rwanda",),
        "uganda": ("uganda",),
        "tanzania": ("tanzania",),
        "zambia": ("zambia",),
        "senegal": ("senegal",),
        "togo": ("togo",),
        "benin": ("benin",),
        "mali": ("mali",),
        "niger": ("niger",),
        "burkina faso": ("burkina faso",),
        "cote d'ivoire": ("cote d'ivoire", "côte d'ivoire", "ivory coast"),
        "ivory coast": ("ivory coast", "côte d'ivoire", "cote d'ivoire"),
        "cameroon": ("cameroon",),
        "democratic republic of the congo": ("democratic republic of the congo", "drc", "rdc"),
        "congo": ("congo",),
        "somalia": ("somalia",),
        "sudan": ("sudan",),
        "south sudan": ("south sudan",),
        "madagascar": ("madagascar",),
        "malawi": ("malawi",),
        "mozambique": ("mozambique",),
        "angola": ("angola",),
        "botswana": ("botswana",),
        "namibia": ("namibia",),
        "zimbabwe": ("zimbabwe",),
        "liberia": ("liberia",),
        "sierra leone": ("sierra leone",),
        "guinea": ("guinea",),
        "guinea-bissau": ("guinea-bissau",),
        "gambia": ("gambia",),
        "gabon": ("gabon",),
        "equatorial guinea": ("equatorial guinea",),
        "central african republic": ("central african republic", "car", "rca"),
        "chad": ("chad",),
        "mauritania": ("mauritania",),
        "morocco": ("morocco",),
        "tunisia": ("tunisia",),
        "algeria": ("algeria",),
        "libya": ("libya",),
        "djibouti": ("djibouti",),
        "eritrea": ("eritrea",),
        "burundi": ("burundi",),
        "comoros": ("comoros",),
        "eswatini": ("eswatini", "swaziland"),
        "lesotho": ("lesotho",),
        "mauritius": ("mauritius",),
        "seychelles": ("seychelles",),
        "cape verde": ("cape verde",),
        "sao tome and principe": ("sao tome and principe",),
        "sao tome": ("sao tome",),
    }

    def __init__(self, fetch_text=None):
        self._fetch_text = fetch_text or self._default_fetch_text

    def discover(self, country, categories=None, query=None, limit=20):
        country = str(country or "").strip()
        if not country:
            return []

        allowed = {
            str(value).strip().lower()
            for value in (categories or [])
            if str(value).strip()
        }
        if allowed and not allowed.intersection({"procurement", "consulting"}):
            return []

        aliases = self._aliases_for(country)
        query_text = str(query or "").strip().lower()
        html = self._fetch_text(self.SOURCE_URL)

        parser = _AfDBProcurementParser()
        parser.feed(html)

        results = []
        seen = set()
        for href, title in parser.items:
            normalized_title = " ".join(title.lower().split())
            if not normalized_title.startswith(self.NOTICE_PREFIXES):
                continue
            if not self._matches_country(normalized_title, aliases):
                if "multinational" not in normalized_title:
                    continue
            category = "consulting" if normalized_title.startswith(("eoi -", "ami -")) else "procurement"
            if allowed and category not in allowed:
                continue
            if query_text and query_text not in normalized_title:
                continue

            opportunity_url = urljoin(self.BASE_URL, href)
            key = opportunity_url or normalized_title
            if key in seen:
                continue
            seen.add(key)

            results.append(self._normalize(title, opportunity_url, country, category))
            if len(results) >= max(1, min(int(limit), 20)):
                break

        return results

    def _normalize(self, title, url, requested_country, category):
        return {
            "title": title[:500],
            "organization": "African Development Bank Group",
            "country": requested_country,
            "category": category,
            "deadline": "",
            "url": url,
            "description": f"Official African Development Bank procurement or consulting notice: {title}",
            "eligible_countries": "African Development Bank member countries; see notice for specific eligibility.",
            "opportunity_type": "Consulting notice" if category == "consulting" else "Procurement notice",
            "funding_amount": "",
            "application_url": url,
            "source_url": self.SOURCE_URL,
            "verification_status": "official_source",
            "source_id": self.SOURCE_ID,
            "source_reliability": "official",
            "eligibility_basis": "Published on the official African Development Bank procurement portal.",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    def _aliases_for(self, country):
        normalized = country.strip().lower()
        return self.COUNTRY_ALIASES.get(normalized, (normalized,))

    @staticmethod
    def _matches_country(title, aliases):
        return any(alias in title for alias in aliases)

    @staticmethod
    def _default_fetch_text(url):
        request = Request(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml",
                "User-Agent": "Open-Radar/1.0",
            },
            method="GET",
        )
        with urlopen(request, timeout=12) as response:
            return response.read().decode("utf-8", errors="replace")
