from open_radar.opportunity_deduplicator import OpportunityDeduplicator
from open_radar.opportunity_ingestion import OpportunityIngestion
from open_radar.opportunity_radar_engine import OpportunityRadarEngine
from open_radar.opportunity_world_bank_source import OpportunityWorldBankSource


class OpportunityDiscoveryService:
    """Discover live World Bank opportunities and run the Radar pipeline."""

    MAX_LIMIT = 20
    SUPPORTED_CATEGORIES = {
        "startup",
        "grant",
        "accelerator",
        "fellowship",
        "scholarship",
        "job",
        "procurement",
        "consulting",
    }

    def __init__(
        self,
        radar_engine=None,
        ingestion=None,
        deduplicator=None,
        world_bank_source=None,
    ):
        self.radar_engine = radar_engine or OpportunityRadarEngine()
        self.ingestion = ingestion or OpportunityIngestion()
        self.deduplicator = deduplicator or OpportunityDeduplicator()
        self.world_bank_source = world_bank_source or OpportunityWorldBankSource()

    def discover(self, country, categories=None, query=None, limit=10):
        country = self._validate_country(country)
        categories = self._normalize_categories(categories)
        limit = max(1, min(int(limit), self.MAX_LIMIT))

        raw = self.world_bank_source.discover(
            country=country,
            categories=categories,
            query=query,
            limit=limit,
        )
        normalized = self.ingestion.normalize_many(raw)
        deduplicated = self.deduplicator.deduplicate(normalized)
        analysis = self.radar_engine.analyze(
            deduplicated[:limit],
            country=country,
        )

        return {
            **analysis,
            "query": {
                "country": country,
                "categories": categories,
                "query": query.strip() if isinstance(query, str) else "",
                "limit": limit,
            },
            "sources": [
                {
                    "id": "world-bank",
                    "name": "World Bank Group",
                    "reliability": "official",
                    "status": "live",
                }
            ],
        }

    def _normalize_categories(self, categories):
        if categories is None:
            return []
        if not isinstance(categories, list):
            raise ValueError("categories_must_be_list")

        result = []
        for value in categories:
            if not isinstance(value, str):
                raise ValueError("categories_must_contain_strings")
            value = value.strip().lower()
            if not value:
                continue
            if value not in self.SUPPORTED_CATEGORIES:
                raise ValueError(f"unsupported_category:{value}")
            if value not in result:
                result.append(value)
        return result

    @staticmethod
    def _validate_country(country):
        if not isinstance(country, str) or not country.strip():
            raise ValueError("country_required")
        return country.strip()
