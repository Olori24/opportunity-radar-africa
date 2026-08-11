from open_radar.opportunity_eu_source import OpportunityEUSource


def test_eu_source_normalizes_grant_results():
    payload = {
        "results": [
            {
                "content": "DIGITAL-2026-AI-DATA-10",
                "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/DIGITAL-2026-AI-DATA-10",
                "metadata": {
                    "title": "DIGITAL-2026-AI-DATA-10",
                    "callIdentifier": "DIGITAL-2026-AI-DATA-10",
                    "deadlineDate": "2026-10-01",
                    "type": "1",
                    "description": "Call for proposals for AI data.",
                },
            }
        ]
    }

    source = OpportunityEUSource(fetch_json=lambda **kwargs: payload)
    results = source.discover("Nigeria", categories=["grant"])

    assert len(results) == 1
    assert results[0]["organization"] == "European Commission / EU Funding & Tenders Portal"
    assert results[0]["source_id"] == "european-union-funding-tenders"
    assert results[0]["verification_status"] == "official_source"
    assert results[0]["source_reliability"] == "official"
    assert results[0]["deadline"] == "2026-10-01"
    assert results[0]["source_notice_id"] == "DIGITAL-2026-AI-DATA-10"


def test_eu_source_builds_country_and_query_search_text():
    calls = []

    def fetch_json(**kwargs):
        calls.append(kwargs)
        return {"results": []}

    source = OpportunityEUSource(fetch_json=fetch_json)
    source.discover("Nigeria", categories=["grant", "procurement"], query="artificial intelligence", limit=7)

    assert len(calls) == 1
    assert calls[0]["text"] == "Nigeria artificial intelligence"
    assert calls[0]["limit"] == 7
    assert calls[0]["query"]["bool"]["must"][0]["terms"]["type"] == ["0", "1"]
    assert calls[0]["query"]["bool"]["must"][1]["terms"]["status"] == [
        "31094501",
        "31094502",
    ]


def test_eu_source_skips_network_for_job_only_requests():
    called = []

    def fetch_json(**kwargs):
        called.append(kwargs)
        return {"results": []}

    source = OpportunityEUSource(fetch_json=fetch_json)
    assert source.discover("Nigeria", categories=["job"]) == []
    assert called == []


def test_eu_source_supports_unfiltered_grants_and_tenders():
    calls = []

    def fetch_json(**kwargs):
        calls.append(kwargs)
        return {"results": []}

    source = OpportunityEUSource(fetch_json=fetch_json)
    source.discover("Nigeria")

    assert calls[0]["query"]["bool"]["must"][0]["terms"]["type"] == [
        "0",
        "1",
        "2",
        "8",
    ]
