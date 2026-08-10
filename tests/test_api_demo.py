import asyncio
import json

from open_radar.api import OpenRadarAPI


def request(path, payload):
    messages = []
    sent = False
    body = json.dumps(payload).encode()

    async def receive():
        nonlocal sent
        if sent:
            return {
                "type": "http.request",
                "body": b"",
                "more_body": False,
            }
        sent = True
        return {
            "type": "http.request",
            "body": body,
            "more_body": False,
        }

    async def send(message):
        messages.append(message)

    asyncio.run(
        OpenRadarAPI(
            service=FakeService(),
            api_key="private-key",
        )(
            {
                "type": "http",
                "method": "POST",
                "path": path,
                "headers": [],
            },
            receive,
            send,
        )
    )
    return messages


class FakeService:
    def analyze_raw(self, opportunities, country):
        return {
            "opportunities": opportunities,
            "recommendation": {
                "recommendation": "apply",
                "opportunity": opportunities[0] if opportunities else None,
                "confidence": 0.9,
            },
            "explanation": {
                "summary": f"Analyzed {len(opportunities)} opportunities for {country}.",
            },
        }


def response_body(messages):
    return json.loads(messages[-1]["body"].decode())


def test_demo_analyze_is_public_and_returns_analysis():
    messages = request(
        "/v1/demo/analyze",
        {
            "country": "Nigeria",
            "opportunities": [
                {"title": "AI Grant", "country": "Nigeria"},
            ],
        },
    )

    assert messages[0]["status"] == 200
    assert response_body(messages)["opportunities"][0]["title"] == "AI Grant"


def test_demo_analyze_limits_opportunities():
    messages = request(
        "/v1/demo/analyze",
        {
            "country": "Nigeria",
            "opportunities": [{"title": str(i)} for i in range(26)],
        },
    )

    assert messages[0]["status"] == 400
    assert response_body(messages)["error"] == "demo_opportunity_limit_exceeded"


def test_demo_analyze_does_not_require_api_key():
    messages = request(
        "/demo/analyze",
        {
            "country": "Nigeria",
            "opportunities": [],
        },
    )

    assert messages[0]["status"] == 200
