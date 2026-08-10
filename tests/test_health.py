from src.api.health import health


def test_health():
    result = health()

    assert result["status"] == "healthy"
    assert result["service"] == "Opportunity Radar Africa"
