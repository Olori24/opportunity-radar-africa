from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.request import Request, urlopen


class _TextParser(HTMLParser):
    """Extract visible text from an official programme page."""

    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if not self._skip_depth:
            value = " ".join(data.split())
            if value:
                self.parts.append(value)

    def text(self):
        return " ".join(self.parts)


class OpportunityNigeriaOfficialSource:
    """
    Discover live opportunities from official Nigerian programme portals.

    Records are emitted only when the official page is reachable and
    contains the expected programme signals. No third-party listings are
    scraped by this source.
    """

    SOURCE_ID = "nigeria-official-programmes"
    COUNTRY = "Nigeria"

    PROGRAMMES = (
        {
            "id": "student-venture-capital-grant",
            "title": "Student Venture Capital Grant (S-VCG)",
            "organization": "Federal Ministry of Education",
            "category": "grant",
            "opportunity_type": "Grant",
            "funding_amount": "₦50,000,000",
            "url": "https://www.svcg.education.gov.ng/",
            "description": "Government-backed funding, validation, mentorship and visibility for student-led businesses and innovations across Nigeria.",
            "required_signals": ("apply now", "₦50m", "student venture capital"),
        },
        {
            "id": "smedan-matching-fund",
            "title": "SMEDAN Matching Fund",
            "organization": "Small and Medium Enterprises Development Agency of Nigeria",
            "category": "grant",
            "opportunity_type": "Funding programme",
            "funding_amount": "Varies",
            "url": "https://www.funds.smedan.gov.ng/",
            "description": "Official SMEDAN portal for Nigerian MSMEs to register, verify and access government-backed funding, mentorship and grant programmes.",
            "required_signals": ("start application", "government-backed programmes", "access funding"),
        },
        {
            "id": "smedan-conditional-grant-scheme",
            "title": "SMEDAN Conditional Grant Scheme for Micro Enterprises",
            "organization": "Small and Medium Enterprises Development Agency of Nigeria",
            "category": "grant",
            "opportunity_type": "Grant",
            "funding_amount": "₦50,000",
            "url": "https://smedan.gov.ng/our-programs/cgs/",
            "description": "Government initiative providing conditional grants to qualifying nano businesses to support workforce and equipment needs.",
            "required_signals": ("₦50,000", "register, benefit, thrive", "conditional grant scheme"),
        },
        {
            "id": "ihatch-cohort-4",
            "title": "iHatch for Startups Cohort 4",
            "organization": "Federal Government Startup Programme",
            "category": "accelerator",
            "opportunity_type": "Incubation programme",
            "funding_amount": "Funding opportunities",
            "url": "https://programs.startup.gov.ng/ihatch/",
            "description": "Five-month incubation programme for Nigerian innovators with training, coworking, mentorship and funding opportunities.",
            "required_signals": ("cohort 4", "operating in nigeria", "funding opportunities"),
        },
        {
            "id": "boi-msme-financing",
            "title": "Bank of Industry SME Financing",
            "organization": "Bank of Industry",
            "category": "startup",
            "opportunity_type": "Loan and business support",
            "funding_amount": "Varies",
            "url": "https://www.boi.ng/who-we-serve/msmes/",
            "description": "Official BOI financing and advisory support for Nigerian SMEs, including project-based lending, matching funds and sector-specific products.",
            "required_signals": ("small and medium enterprise", "lending services", "apply now"),
        },
    )

    def __init__(self, fetch_text=None):
        self._fetch_text = fetch_text or self._default_fetch_text

    def discover(self, country, categories=None, query=None, limit=20):
        if str(country or "").strip().lower() != self.COUNTRY.lower():
            return []

        allowed = {
            str(category).strip().lower()
            for category in (categories or [])
            if str(category).strip()
        }
        query_text = str(query or "").strip().lower()
        results = []

        for programme in self.PROGRAMMES:
            if allowed and programme["category"] not in allowed:
                continue

            try:
                page = self._fetch_text(programme["url"])
            except Exception:
                continue

            normalized_page = " ".join(page.lower().split())
            if not all(signal.lower() in normalized_page for signal in programme["required_signals"]):
                continue

            searchable = " ".join(
                [programme["title"], programme["organization"], programme["description"], normalized_page]
            ).lower()
            if query_text and query_text not in searchable:
                continue

            results.append(self._normalize(programme))
            if len(results) >= max(1, min(int(limit), 20)):
                break

        return results

    def _normalize(self, programme):
        return {
            "title": programme["title"],
            "organization": programme["organization"],
            "country": self.COUNTRY,
            "category": programme["category"],
            "deadline": "",
            "url": programme["url"],
            "description": programme["description"],
            "eligible_countries": self.COUNTRY,
            "opportunity_type": programme["opportunity_type"],
            "funding_amount": programme["funding_amount"],
            "application_url": programme["url"],
            "source_url": programme["url"],
            "verification_status": "verified",
            "source_id": self.SOURCE_ID,
            "source_reliability": "official",
            "eligibility_basis": "Official programme page states Nigerian participation or access.",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

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
            raw = response.read().decode("utf-8", errors="replace")

        parser = _TextParser()
        parser.feed(raw)
        return parser.text()
