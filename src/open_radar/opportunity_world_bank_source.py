from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json


class OpportunityWorldBankSource:
    """Read live World Bank procurement notices into Open Radar's schema."""

    BASE_URL = "https://search.worldbank.org/api/v2/procnotices"
    SOURCE_URL = "https://projects.worldbank.org/en/projects-operations/procurement"
    SOURCE_ID = "world-bank"

    CATEGORY_QUERIES = {
        "procurement": "",
        "consulting": "consulting",
        "consultancy": "consulting",
        "grant": "grant",
        "startup": "startup",
        "accelerator": "accelerator",
        "fellowship": "fellowship",
        "scholarship": "scholarship",
        "job": "consultant",
    }

    def __init__(self, fetch_json=None):
        self._fetch_json = fetch_json or self._default_fetch_json

    def discover(self, country, categories=None, query=None, limit=20):
        params = {
            "format": "json",
            "rows": max(1, min(int(limit), 50)),
            "os": 0,
            "project_ctry_name": country,
        }

        search_terms = []
        for category in categories or []:
            term = self.CATEGORY_QUERIES.get(str(category).strip().lower())
            if term:
                search_terms.append(term)

        if query and isinstance(query, str) and query.strip():
            search_terms.append(query.strip())

        if search_terms:
            params["qterm"] = " ".join(dict.fromkeys(search_terms))

        payload = self._fetch_json(
            self.BASE_URL + "?" + urlencode(params)
        )

        if not isinstance(payload, dict):
            return []

        records = payload.get("procnotices", [])
        if isinstance(records, dict):
            records = list(records.values())
        if not isinstance(records, list):
            return []

        return [
            self._normalize(record)
            for record in records
            if isinstance(record, dict)
        ]

    def _normalize(self, record):
        notice_id = str(record.get("id") or "").strip()
        title = self._clean(
            record.get("notice_text")
            or record.get("project_name")
            or record.get("notice_type")
            or "World Bank procurement opportunity"
        )
        country = self._clean(record.get("project_ctry_name") or "")
        deadline = self._clean(
            record.get("submission_deadline_date")
            or record.get("deadline_date")
            or ""
        )
        description = self._clean(
            record.get("notice_text")
            or record.get("project_name")
            or ""
        )

        opportunity_url = ""
        if notice_id:
            opportunity_url = (
                "https://projects.worldbank.org/en/projects-operations/"
                f"procurement-detail/{notice_id}"
            )

        notice_type = self._clean(record.get("notice_type") or "procurement")
        category = (
            "consulting"
            if "expression of interest" in notice_type.lower()
            or "consult" in title.lower()
            else "procurement"
        )

        return {
            "title": title[:500],
            "organization": "World Bank Group",
            "country": country,
            "category": category,
            "deadline": deadline,
            "url": opportunity_url,
            "description": description[:3000],
            "eligible_countries": country,
            "opportunity_type": notice_type,
            "funding_amount": self._clean(record.get("estimated_value") or ""),
            "application_url": opportunity_url,
            "source_url": self.SOURCE_URL,
            "verification_status": "official_source",
            "source_id": self.SOURCE_ID,
            "source_reliability": "official",
            "published_date": self._clean(
                record.get("noticedate") or record.get("publication_date") or ""
            ),
            "source_notice_id": notice_id,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _clean(value):
        if value is None:
            return ""
        return " ".join(str(value).replace("\n", " ").split())

    @staticmethod
    def _default_fetch_json(url):
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Open-Radar/1.0",
            },
            method="GET",
        )
        with urlopen(request, timeout=12) as response:
            return json.loads(response.read().decode("utf-8"))
