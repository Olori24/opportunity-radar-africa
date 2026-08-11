from open_radar.opportunity_discovery_service import OpportunityDiscoveryService


class FakeSource:
    def __init__(self):
        self.calls = []

    def discover(self, country, categories=None, query=None, limit=20):
        self.calls.append((country, categories, query, limit))
        return [
            {
                "title": "Tender A",
                "organization": "World Bank Group",
                "country": country,
                "category": "procurement",
                "deadline": "2026-12-31",
            },
            {
                "title": "Tender A",
                "organization": "World Bank Group",
                "country": country,
                "category": "procurement",
                "deadline": "2026-12-31",
            },
        ]


class FakeIngestion:
    def normalize_many(self, opportunities):
        return [dict(item, normalized=True) for item in opportunities]


class FakeDeduplicator:
    def deduplicate(self, opportunities):
        return opportunities[:1]


class FakeEngine:
    def analyze(self, opportunities, country):
        return {
            "opportunities": opportunities,
            "recommendation": {"recommendation": "apply"},
            "explanation": {"summary": "Good match."},
        }


def test_discovery_runs_source_normalization_deduplication_and_analysis():
    source = FakeSource()
    service = OpportunityDiscoveryService(
        radar_engine=FakeEngine(),
        ingestion=FakeIngestion(),
        deduplicator=FakeDeduplicator(),
        world_bank_source=source,
    )

    result = service.discover(
        country="Nigeria",
        categories=["procurement"],
        query="digital",
        limit=5,
    )

    assert len(result["opportunities"]) == 1
    assert result["opportunities"][0]["normalized"] is True
    assert result["query"] == {
        "country": "Nigeria",
        "categories": ["procurement"],
        "query": "digital",
        "limit": 5,
    }
    assert result["sources"][0]["id"] == "world-bank"
    assert source.calls == [
        ("Nigeria", ["procurement"], "digital", 5)
    ]


def test_discovery_rejects_unknown_category():
    service = OpportunityDiscoveryService(
        radar_engine=FakeEngine(),
        ingestion=FakeIngestion(),
        deduplicator=FakeDeduplicator(),
        world_bank_source=FakeSource(),
    )

    try:
        service.discover("Nigeria", categories=["unknown"])
    except ValueError as exc:
        assert str(exc) == "unsupported_category:unknown"
    else:
        raise AssertionError("Expected unsupported category error")
