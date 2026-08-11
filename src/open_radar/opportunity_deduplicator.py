import hashlib
from urllib.parse import urlparse, urlunparse


class OpportunityDeduplicator:
    """
    Deterministically identify and remove duplicate opportunities.

    Identity priority:
    1. Canonical application URL
    2. Canonical opportunity URL
    3. Organization + title + deadline

    The first occurrence wins and input objects are never mutated.
    """

    def deduplicate(self, opportunities):
        if not opportunities:
            return []

        seen = set()
        result = []

        for opportunity in opportunities:
            if not isinstance(opportunity, dict):
                continue

            identity = self.identity(opportunity)
            if identity in seen:
                continue

            seen.add(identity)
            result.append(dict(opportunity))

        return result

    def identity(self, opportunity):
        application_url = self._canonical_url(
            opportunity.get("application_url")
        )
        if application_url:
            return f"application:{application_url}"

        opportunity_url = self._canonical_url(
            opportunity.get("url")
        )
        if opportunity_url:
            return f"url:{opportunity_url}"

        organization = self._normalize_text(
            opportunity.get("organization")
        )
        title = self._normalize_text(
            opportunity.get("title")
        )
        deadline = self._normalize_text(
            opportunity.get("deadline")
        )

        raw_identity = "|".join(
            [organization, title, deadline]
        )

        digest = hashlib.sha256(
            raw_identity.encode("utf-8")
        ).hexdigest()

        return f"composite:{digest}"

    def _canonical_url(self, value):
        if not isinstance(value, str):
            return ""

        value = value.strip()
        if not value:
            return ""

        try:
            parsed = urlparse(value)
        except ValueError:
            return ""

        if parsed.scheme not in {"http", "https"}:
            return ""

        if not parsed.netloc:
            return ""

        hostname = (parsed.hostname or "").lower().rstrip(".")
        if not hostname:
            return ""

        path = parsed.path.rstrip("/") or "/"

        return urlunparse(
            (
                parsed.scheme.lower(),
                hostname,
                path,
                "",
                parsed.query,
                "",
            )
        )

    def _normalize_text(self, value):
        if value is None:
            return ""

        return " ".join(str(value).lower().split())
