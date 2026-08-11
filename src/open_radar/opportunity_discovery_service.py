from open_radar.opportunity_afdb_source import OpportunityAfDBSource
from open_radar.opportunity_deduplicator import OpportunityDeduplicator
from open_radar.opportunity_eu_source import OpportunityEUSource
from open_radar.opportunity_ingestion import OpportunityIngestion
from open_radar.opportunity_nigeria_official_source import OpportunityNigeriaOfficialSource
from open_radar.opportunity_radar_engine import OpportunityRadarEngine
from open_radar.opportunity_world_bank_source import OpportunityWorldBankSource


class OpportunityDiscoveryService:
    """Discover live opportunities from approved official sources."""

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
        nigeria_official_source=None,
        afdb_source=None,
        eu_source=None,
    ):
        self.radar_engine = radar_engine or OpportunityRadarEngine()
        self.ingestion = ingestion or OpportunityIngestion()
        self.deduplicator = deduplicator or OpportunityDeduplicator()
        self.world_bank_source = world_bank_source or OpportunityWorldBankSource()
        self.nigeria_official_source = (
            nigeria_official_source or OpportunityNigeriaOfficialSource()
        )
        self.afdb_source = afdb_source or OpportunityAfDBSource()
        self.eu_source = eu_source or OpportunityEUSource()

    def discover(self, country, categories=None, query=None, limit=10):
        country = self._validate_country(country)
        categories = self._normalize_categories(categories)
        limit = max(1, min(int(limit), self.MAX_LIMIT))

        raw = []
        sources = []

        try:
            official_nigeria = self.nigeria_official_source.discover(
                country=country,
                categories=categories,
                query=query,
                limit=limit,
            )
            raw.extend(official_nigeria)
            if official_nigeria:
                sources.append({
                    "id": "nigeria-official-programmes",
                    "name": "Official Nigerian Government & DFI Programmes",
                    "reliability": "official",
                    "status": "live",
                    "count": len(official_nigeria),
                })
        except Exception:
            sources.append({
                "id": "nigeria-official-programmes",
                "name": "Official Nigerian Government & DFI Programmes",
                "reliability": "official",
                "status": "error",
                "count": 0,
            })

        try:
            world_bank = self.world_bank_source.discover(
                country=country,
                categories=categories,
                query=query,
                limit=limit,
            )
            raw.extend(world_bank)
            sources.append({
                "id": "world-bank",
                "name": "World Bank Group",
                "reliability": "official",
                "status": "live",
                "count": len(world_bank),
            })
        except Exception:
            sources.append({
                "id": "world-bank",
                "name": "World Bank Group",
                "reliability": "official",
                "status": "error",
                "count": 0,
            })

        try:
            afdb = self.afdb_source.discover(
                country=country,
                categories=categories,
                query=query,
                limit=limit,
            )
            raw.extend(afdb)
            sources.append({
                "id": "afdb-procurement",
                "name": "African Development Bank Group",
                "reliability": "official",
                "status": "live",
                "count": len(afdb),
            })
        except Exception:
            sources.append({
                "id": "afdb-procurement",
                "name": "African Development Bank Group",
                "reliability": "official",
                "status": "error",
                "count": 0,
            })

        try:
            eu = self.eu_source.discover(
                country=country,
                categories=categories,
                query=query,
                limit=limit,
            )
            raw.extend(eu)
            sources.append({
                "id": "european-union-funding-tenders",
                "name": "European Commission Funding & Tenders Portal",
                "reliability": "official",
                "status": "live",
                "count": len(eu),
            })
        except Exception:
            sources.append({
                "id": "european-union-funding-tenders",
                "name": "European Commission Funding & Tenders Portal",
                "reliability": "official",
                "status": "error",
                "count": 0,
            })

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
            "sources": sources,
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
