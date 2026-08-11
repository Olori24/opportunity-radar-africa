from open_radar.opportunity_world_bank_source import OpportunityWorldBankSource


def test_world_bank_source_builds_country_query_and_normalizes_notice():
    calls = []

    def fetch_json(url):
        calls.append(url)
        return {
            "total": "1",
            "procnotices": [
                {
                    "id": "OP00123456",
                    "notice_type": "Request for Expression of Interest",
                    "noticedate": "11-Aug-2026",
                    "notice_status": "Published",
                    "project_ctry_name": "Nigeria",
                    "project_id": "P123456",
                    "project_name": "Digital Skills Consultancy",
                    "notice_text": "Consulting services for digital skills development.",
                    "submission_deadline_date": "2026-09-30T00:00:00Z",
                }
            ],
        }

    source = OpportunityWorldBankSource(fetch_json=fetch_json)
    result = source.discover(
        country="Nigeria",
        categories=["consulting"],
        query="digital skills",
        limit=5,
    )

    assert len(result) == 1
    assert result[0]["title"] == "Consulting services for digital skills development."
    assert result[0]["organization"] == "World Bank Group"
    assert result[0]["country"] == "Nigeria"
    assert result[0]["category"] == "consulting"
    assert result[0]["deadline"] == "2026-09-30T00:00:00Z"
    assert result[0]["source_id"] == "world-bank"
    assert result[0]["verification_status"] == "official_source"
    assert "project_ctry_name=Nigeria" in calls[0]
    assert "digital+skills" in calls[0]


def test_world_bank_source_handles_dict_records():
    def fetch_json(url):
        return {
            "procnotices": {
                "OP1": {"id": "OP1", "project_ctry_name": "Ghana", "notice_text": "Tender"},
                "OP2": {"id": "OP2", "project_ctry_name": "Ghana", "notice_text": "Tender 2"},
            }
        }

    source = OpportunityWorldBankSource(fetch_json=fetch_json)
    result = source.discover("Ghana", limit=2)

    assert len(result) == 2
    assert {item["source_notice_id"] for item in result} == {"OP1", "OP2"}


def test_world_bank_source_returns_empty_for_malformed_payload():
    source = OpportunityWorldBankSource(fetch_json=lambda url: {"procnotices": "bad"})
    assert source.discover("Nigeria") == []
