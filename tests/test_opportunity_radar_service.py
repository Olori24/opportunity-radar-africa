from open_radar.opportunity_radar_service import (
    OpportunityRadarService,
)


class FakeRadarEngine:
    def __init__(self):
        self.calls = []

    def analyze(self, opportunities, country):
        self.calls.append(
            ("analyze", opportunities, country)
        )
        return {"ok": True}

    def analyze_raw(self, opportunities, country):
        self.calls.append(
            ("analyze_raw", opportunities, country)
        )
        return {"raw": True}


class FakeIngestion:
    def normalize_many(self, opportunities):
        return [
            {
                **item,
                "normalized": True,
            }
            for item in opportunities
        ]


class FakeClient:
    class Response:
        status_code = 200

        def json(self):
            return [
                {
                    "name": "Grant A",
                    "country": "Nigeria",
                }
            ]

    def get(self, url):
        return self.Response()


def test_analyze_delegates_to_radar_engine():
    engine = FakeRadarEngine()
    service = OpportunityRadarService(
        radar_engine=engine,
    )

    result = service.analyze(
        [{"title": "Grant A"}],
        country="Nigeria",
    )

    assert result == {"ok": True}
    assert engine.calls == [
        (
            "analyze",
            [{"title": "Grant A"}],
            "Nigeria",
        )
    ]


def test_analyze_raw_delegates_to_radar_engine():
    engine = FakeRadarEngine()
    service = OpportunityRadarService(
        radar_engine=engine,
    )

    result = service.analyze_raw(
        [{"title": "Grant A"}],
        country="Nigeria",
    )

    assert result == {"raw": True}
    assert engine.calls == [
        (
            "analyze_raw",
            [{"title": "Grant A"}],
            "Nigeria",
        )
    ]


def test_fetch_and_analyze_runs_pipeline():
    engine = FakeRadarEngine()
    service = OpportunityRadarService(
        radar_engine=engine,
        ingestion=FakeIngestion(),
    )

    result = service.fetch_and_analyze(
        url="https://example.org/opportunities",
        country="Nigeria",
        client=FakeClient(),
        field_mapping={
            "name": "title",
        },
    )

    assert result == {"ok": True}

    assert engine.calls[0][0] == "analyze"
    assert engine.calls[0][2] == "Nigeria"

    opportunities = engine.calls[0][1]

    assert opportunities[0]["title"] == "Grant A"
    assert opportunities[0]["normalized"] is True
