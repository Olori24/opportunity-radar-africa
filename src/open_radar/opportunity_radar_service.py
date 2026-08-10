from open_radar.opportunity_deduplicator import OpportunityDeduplicator
from open_radar.opportunity_http_transport import OpportunityHttpTransport
from open_radar.opportunity_ingestion import OpportunityIngestion
from open_radar.opportunity_radar_engine import OpportunityRadarEngine
from open_radar.opportunity_source_connector import OpportunitySourceConnector
from open_radar.opportunity_source_parser import OpportunitySourceParser


class OpportunityRadarService:
    """
    Public application boundary for Open Radar.

    Coordinates source acquisition, parsing, ingestion,
    deduplication, intelligence analysis, ranking,
    recommendation, and explanation.
    """

    def __init__(
        self,
        radar_engine=None,
        ingestion=None,
        deduplicator=None,
        source_registry=None,
    ):
        self.radar_engine = radar_engine or OpportunityRadarEngine()
        self.ingestion = ingestion or OpportunityIngestion()
        self.deduplicator = (
            deduplicator or OpportunityDeduplicator()
        )
        self.source_registry = source_registry

    def analyze(self, opportunities, country):
        """
        Analyze already-normalized opportunities.
        """
        return self.radar_engine.analyze(
            opportunities,
            country=country,
        )

    def analyze_raw(self, opportunities, country):
        """
        Normalize and analyze raw opportunity dictionaries.
        """
        return self.radar_engine.analyze_raw(
            opportunities,
            country=country,
        )

    def fetch_and_analyze(
        self,
        url,
        country,
        client,
        field_mapping=None,
    ):
        """
        Fetch, parse, normalize, deduplicate,
        and analyze opportunities from a source.
        """

        transport = OpportunityHttpTransport(client)
        connector = OpportunitySourceConnector(
            transport,
            registry=self.source_registry,
        )

        payload = connector.fetch(url)

        parser = OpportunitySourceParser(
            field_mapping=field_mapping,
        )

        parsed = parser.parse(payload)

        normalized = self.ingestion.normalize_many(
            parsed
        )

        deduplicated = self.deduplicator.deduplicate(
            normalized
        )

        return self.analyze(
            deduplicated,
            country=country,
        )
