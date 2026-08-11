from open_radar.opportunity_afdb_source import OpportunityAfDBSource


def test_afdb_source_filters_country_and_normalizes_notice():
    html = """
    <html><body>
      <a href="/en/projects-and-operations/procurement/eoi-nigeria-a">EOI - Nigeria - Consulting Firm for Digital Transformation</a>
      <a href="/en/projects-and-operations/procurement/eoi-kenya-b">EOI - Kenya - Road Safety Consultant</a>
      <a href="/en/projects-and-operations/procurement/gpn-multinational-c">GPN - Multinational - Regional Digital Programme</a>
      <a href="/about-us">About Us</a>
    </body></html>
    """

    source = OpportunityAfDBSource(fetch_text=lambda url: html)
    results = source.discover(
        country="Nigeria",
        categories=["consulting", "procurement"],
        limit=10,
    )

    assert len(results) == 2
    assert results[0]["title"].startswith("EOI - Nigeria")
    assert results[0]["organization"] == "African Development Bank Group"
    assert results[0]["category"] == "consulting"
    assert results[0]["verification_status"] == "official_source"
    assert results[0]["source_id"] == "afdb-procurement"
    assert results[0]["source_reliability"] == "official"
    assert results[1]["title"].startswith("GPN - Multinational")


def test_afdb_source_query_filters_results():
    html = """
    <a href="/one">EOI - Nigeria - Digital Health Consultant</a>
    <a href="/two">EOI - Nigeria - Agricultural Value Chain Consultant</a>
    """

    source = OpportunityAfDBSource(fetch_text=lambda url: html)
    results = source.discover(
        country="Nigeria",
        categories=["consulting"],
        query="digital health",
        limit=10,
    )

    assert len(results) == 1
    assert "Digital Health" in results[0]["title"]
