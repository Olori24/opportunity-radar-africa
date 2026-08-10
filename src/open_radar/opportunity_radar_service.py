from open_radar.opportunity_http_transport import OpportunityHttpTransport
from open_radar.opportunity_ingestion import OpportunityIngestion
from open_radar.opportunity_radar_engine import OpportunityRadarEngine
from open_radar.opportunity_source_connector import OpportunitySourceConnector
from open_radar.opportunity_source_parser import OpportunitySourceParser


class OpportunityRadarService:
    """
    Public application boundary for Open Radar.

    Coordinates source acquisition, parsing, ingestion,
    intelligence analysis, ranking, recommendation, and explanation.
    """

    def __init__(
        self,
        radar_engine=None,
        ingestion=None,
    ):
        self.radar_engine = radar_engine or OpportunityRadarEngine()
        self.ingestion = ingestion or OpportunityIngestion()

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
        Fetch, parse, normalize, and analyze opportunities from a source.
        """

        transport = OpportunityHttpTransport(client)
        connector = OpportunitySourceConnector(transport)

        payload = connector.fetch(url)

        parser = OpportunitySourceParser(
            field_mapping=field_mapping,
        )

        parsed = parser.parse(payload)
        normalized = self.ingestion.normalize_many(parsed)

        return self.analyze(
            normalized,
            country=country,
        )
