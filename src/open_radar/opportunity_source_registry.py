from urllib.parse import urlparse


class OpportunitySourceRegistry:
    """
    Explicit allowlist of sources Open Radar is permitted to fetch.

    A URL being syntactically valid does not make it an approved source.
    """

    DEFAULT_SOURCES = {
        "world-bank": {
            "domain": "worldbank.org",
            "category": "development",
            "reliability": "official",
            "enabled": True,
        },
        "african-development-bank": {
            "domain": "afdb.org",
            "category": "development",
            "reliability": "official",
            "enabled": True,
        },
        "united-nations": {
            "domain": "un.org",
            "category": "international",
            "reliability": "official",
            "enabled": True,
        },
        "who": {
            "domain": "who.int",
            "category": "public-health",
            "reliability": "official",
            "enabled": True,
        },
        "unesco": {
            "domain": "unesco.org",
            "category": "education",
            "reliability": "official",
            "enabled": True,
        },
        "european-union": {
            "domain": "europa.eu",
            "category": "international",
            "reliability": "official",
            "enabled": True,
        },
        "nigeria-government": {
            "domain": "gov.ng",
            "category": "government",
            "reliability": "official",
            "enabled": True,
        },
        "south-africa-government": {
            "domain": "gov.za",
            "category": "government",
            "reliability": "official",
            "enabled": True,
        },
        "kenya-government": {
            "domain": "gov.ke",
            "category": "government",
            "reliability": "official",
            "enabled": True,
        },
        "ghana-government": {
            "domain": "gov.gh",
            "category": "government",
            "reliability": "official",
            "enabled": True,
        },
    }

    def __init__(self, sources=None):
        self.sources = dict(
            sources if sources is not None else self.DEFAULT_SOURCES
        )

    def is_allowed(self, url):
        source = self.resolve(url)
        return source is not None and source["enabled"] is True

    def resolve(self, url):
        hostname = self._hostname(url)
        if not hostname:
            return None

        for source_id, source in self.sources.items():
            if not source.get("enabled", False):
                continue

            domain = source.get("domain", "").lower().rstrip(".")

            if hostname == domain or hostname.endswith("." + domain):
                result = dict(source)
                result["id"] = source_id
                return result

        return None

    def list_sources(self):
        return [
            {
                "id": source_id,
                **dict(source),
            }
            for source_id, source in self.sources.items()
        ]

    def _hostname(self, url):
        if not isinstance(url, str):
            return ""

        url = url.strip()
        if not url:
            return ""

        try:
            parsed = urlparse(url)
        except ValueError:
            return ""

        if parsed.scheme not in {"http", "https"}:
            return ""

        return (parsed.hostname or "").lower().rstrip(".")
