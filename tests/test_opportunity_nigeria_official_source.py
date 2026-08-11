from open_radar.opportunity_nigeria_official_source import (
    OpportunityNigeriaOfficialSource,
)


def test_discovers_verified_nigerian_programmes_from_live_page_signals():
    pages = {
        "https://www.svcg.education.gov.ng/": (
            "APPLY NOW Student Venture Capital Program ₦50M student venture capital"
        ),
        "https://www.funds.smedan.gov.ng/": (
            "Start Application government-backed programmes access funding"
        ),
    }

    source = OpportunityNigeriaOfficialSource(fetch_text=lambda url: pages[url])
    results = source.discover("Nigeria", categories=["grant"], limit=10)

    assert len(results) == 2
    assert all(item["verification_status"] == "verified" for item in results)
    assert all(item["source_reliability"] == "official" for item in results)
    assert all(item["eligible_countries"] == "Nigeria" for item in results)


def test_non_nigeria_country_returns_no_records():
    source = OpportunityNigeriaOfficialSource(fetch_text=lambda url: "")
    assert source.discover("Ghana") == []


def test_missing_live_signal_is_not_emitted():
    source = OpportunityNigeriaOfficialSource(
        fetch_text=lambda url: "official page but application closed"
    )
    assert source.discover("Nigeria") == []
