from open_radar.opportunity_discovery_service import OpportunityDiscoveryService


class FakeSource:
    def __init__(self, title="Tender A", category="procurement"):
        self.calls = []
        self.title = title
        self.category = category

    def discover(self, country, categories=None, query=None, limit=20):
        self.calls.append((country, categories, query, limit))
        return [
            {
                "title": self.title,
                "organization": "World Bank Group",
                "country": country,
                "category": self.category,
                "deadline": "2026-12-31",
            },
            {
                "title": self.title,
                "organization": "World Bank Group",
                "country": country,
                "category": self.category,
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


def test_discovery_runs_all_sources_normalization_deduplication_and_analysis():
    world_bank = FakeSource()
    nigeria = FakeSource(title="Grant A", category="grant")
    afdb = FakeSource(title="EOI - Nigeria - Consulting A", category="consulting")
    service = OpportunityDiscoveryService(
        radar_engine=FakeEngine(),
        ingestion=FakeIngestion(),
        deduplicator=FakeDeduplicator(),
        world_bank_source=world_bank,
        nigeria_official_source=nigeria,
        afdb_source=afdb,
    )

    result = service.discover(
        country="Nigeria",
        categories=["procurement", "grant"],
        query="digital",
        limit=5,
    )

    assert len(result["opportunities"]) == 1
    assert result["opportunities"][0]["normalized"] is True
    assert result["query"] == {
        "country": "Nigeria",
        "categories": ["procurement", "grant"],
        "query": "digital",
        "limit": 5,
    }
    assert {source["id"] for source in result["sources"]} == {
        "world-bank",
        "nigeria-official-programmes",
        "afdb-procurement",
    }
    assert world_bank.calls == [("Nigeria", ["procurement", "grant"], "digital", 5)]
    assert nigeria.calls == [("Nigeria", ["procurement", "grant"], "digital", 5)]
    assert afdb.calls == [("Nigeria", ["procurement", "grant"], "digital", 5)]


def test_discovery_accepts_public_opportunity_categories():
    source = FakeSource()
    nigeria = FakeSource(title="Grant A", category="grant")
    afdb = FakeSource()
    service = OpportunityDiscoveryService(
        radar_engine=FakeEngine(),
        ingestion=FakeIngestion(),
        deduplicator=FakeDeduplicator(),
        world_bank_source=source,
        nigeria_official_source=nigeria,
        afdb_source=afdb,
    )

    categories = [
        "startup",
        "grant",
        "accelerator",
        "fellowship",
        "scholarship",
        "job",
        "procurement",
        "consulting",
    ]

    result = service.discover("Nigeria", categories=categories, limit=5)

    assert result["query"]["categories"] == categories
    assert source.calls == [("Nigeria", categories, None, 5)]
    assert nigeria.calls == [("Nigeria", categories, None, 5)]
    assert afdb.calls == [("Nigeria", categories, None, 5)]


def test_discovery_normalizes_and_deduplicates_categories():
    service = OpportunityDiscoveryService(
        radar_engine=FakeEngine(),
        ingestion=FakeIngestion(),
        deduplicator=FakeDeduplicator(),
        world_bank_source=FakeSource(),
        nigeria_official_source=FakeSource(title="Grant A", category="grant"),
        afdb_source=FakeSource(),
    )

    result = service.discover(
        "Nigeria",
        categories=[" Startup ", "startup", "GRANT", "grant"],
    )

    assert result["query"]["categories"] == ["startup", "grant"]


def test_discovery_rejects_unknown_category():
    service = OpportunityDiscoveryService(
        radar_engine=FakeEngine(),
        ingestion=FakeIngestion(),
        deduplicator=FakeDeduplicator(),
        world_bank_source=FakeSource(),
        nigeria_official_source=FakeSource(title="Grant A", category="grant"),
        afdb_source=FakeSource(),
    )

    try:
        service.discover("Nigeria", categories=["unknown"])
    except ValueError as exc:
        assert str(exc) == "unsupported_category:unknown"
    else:
        raise AssertionError("Expected unsupported category error")
