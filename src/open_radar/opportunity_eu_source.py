from datetime import datetime, timezone
import json
import uuid
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class OpportunityEUSource:
    """Read public EU Funding & Tenders Portal opportunities via its REST API."""

    SOURCE_ID = "european-union-funding-tenders"
    SOURCE_URL = "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/home"
    API_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
    API_KEY = "SEDIA"

    SEARCHABLE_CATEGORIES = {
        "grant",
        "startup",
        "accelerator",
        "fellowship",
        "scholarship",
        "procurement",
        "consulting",
    }

    # Funding & Tenders reference codes documented by the European Commission.
    TYPE_CODES = {
        "procurement": "0",
        "grant": "1",
        "fellowship": "2",
        "cascade": "8",
    }

    STATUS_CODES = {
        "forthcoming": "31094501",
        "open": "31094502",
        "closed": "31094503",
    }

    def __init__(self, fetch_json=None):
        self._fetch_json = fetch_json or self._default_fetch_json

    def discover(self, country, categories=None, query=None, limit=20):
        country = str(country or "").strip()
        if not country:
            return []

        allowed = {
            str(value).strip().lower()
            for value in (categories or [])
            if str(value).strip()
        }

        if allowed and not allowed.intersection(self.SEARCHABLE_CATEGORIES):
            return []

        type_codes = self._type_codes(allowed)
        text = country
        if isinstance(query, str) and query.strip():
            text = f"{country} {query.strip()}"

        query_data = {
            "bool": {
                "must": [
                    {"terms": {"type": type_codes}},
                    {
                        "terms": {
                            "status": [
                                self.STATUS_CODES["forthcoming"],
                                self.STATUS_CODES["open"],
                            ]
                        }
                    },
                ]
            }
        }

        payload = self._fetch_json(
            text=text,
            query=query_data,
            limit=max(1, min(int(limit), 20)),
        )

        if not isinstance(payload, dict):
            return []

        records = payload.get("results", [])
        if not isinstance(records, list):
            return []

        results = []
        seen = set()
        for record in records:
            normalized = self._normalize(record, country, allowed)
            if not normalized:
                continue

            key = normalized.get("source_notice_id") or normalized.get("url") or normalized["title"]
            if key in seen:
                continue
            seen.add(key)
            results.append(normalized)

            if len(results) >= max(1, min(int(limit), 20)):
                break

        return results

    def _type_codes(self, categories):
        if not categories:
            return ["0", "1", "2", "8"]

        codes = []
        if categories.intersection({"procurement", "consulting"}):
            codes.append("0")
        if categories.intersection({"grant", "startup", "accelerator", "scholarship"}):
            codes.append("1")
        if "fellowship" in categories:
            codes.append("2")

        return list(dict.fromkeys(codes or ["0", "1", "2", "8"]))

    def _normalize(self, record, requested_country, allowed):
        if not isinstance(record, dict):
            return None

        metadata = record.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        title = self._clean(
            record.get("content")
            or metadata.get("title")
            or metadata.get("callIdentifier")
            or "EU Funding & Tenders opportunity"
        )
        url = self._clean(record.get("url") or "")
        identifier = self._clean(
            metadata.get("callIdentifier")
            or metadata.get("identifier")
            or metadata.get("topicIdentifier")
            or ""
        )
        deadline = self._clean(
            metadata.get("deadlineDate")
            or metadata.get("deadline")
            or metadata.get("submissionDeadline")
            or ""
        )
        description = self._clean(
            metadata.get("description")
            or record.get("description")
            or record.get("content")
            or ""
        )

        type_value = self._clean(metadata.get("type") or record.get("type") or "")
        category = self._category(type_value, title, allowed)

        return {
            "title": title[:500],
            "organization": "European Commission / EU Funding & Tenders Portal",
            "country": requested_country,
            "category": category,
            "deadline": deadline,
            "url": url,
            "description": description[:3000],
            "eligible_countries": "Eligibility varies by call; see the official call conditions.",
            "opportunity_type": type_value or "EU funding or tender opportunity",
            "funding_amount": self._clean(
                metadata.get("budget")
                or metadata.get("maxGrantAmount")
                or metadata.get("estimatedValue")
                or ""
            ),
            "application_url": url,
            "source_url": self.SOURCE_URL,
            "verification_status": "official_source",
            "source_id": self.SOURCE_ID,
            "source_reliability": "official",
            "source_notice_id": identifier,
            "published_date": self._clean(
                metadata.get("publicationDate")
                or metadata.get("startDate")
                or ""
            ),
            "eligibility_basis": "Retrieved from the official European Commission Funding & Tenders Portal public REST API.",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _category(type_value, title, allowed):
        value = f"{type_value} {title}".lower()
        if "consult" in value:
            category = "consulting"
        elif "tender" in value or "procurement" in value:
            category = "procurement"
        elif "fellow" in value or type_value == "2":
            category = "fellowship"
        else:
            category = "grant"

        if allowed and category not in allowed:
            if category == "grant" and allowed.intersection({"startup", "accelerator", "scholarship"}):
                return next(iter(allowed.intersection({"startup", "accelerator", "scholarship"})))
            return category
        return category

    @staticmethod
    def _clean(value):
        if value is None:
            return ""
        if isinstance(value, (list, tuple)):
            value = " ".join(str(item) for item in value)
        return " ".join(str(value).replace("\n", " ").split())

    @classmethod
    def _default_fetch_json(cls, text, query, limit):
        boundary = "----OpenRadar" + uuid.uuid4().hex
        params = urlencode(
            {
                "apiKey": cls.API_KEY,
                "text": text or "*",
                "pageSize": str(limit),
                "pageNumber": "1",
            }
        )

        fields = {
            "query": json.dumps(query),
            "languages": json.dumps(["en"]),
            "sort": json.dumps({"field": "sortStatus", "order": "ASC"}),
        }

        body_parts = []
        for name, value in fields.items():
            body_parts.extend(
                [
                    f"--{boundary}",
                    f'Content-Disposition: form-data; name="{name}"',
                    "Content-Type: application/json",
                    "",
                    value,
                ]
            )
        body_parts.append(f"--{boundary}--")
        body = "\r\n".join(body_parts).encode("utf-8")

        request = Request(
            f"{cls.API_URL}?{params}",
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "Open-Radar/1.0",
            },
            method="POST",
        )
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
