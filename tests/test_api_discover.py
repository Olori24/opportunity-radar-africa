import asyncio
import json

from open_radar.api import OpenRadarAPI


class FakeDiscoveryService:
    def __init__(self):
        self.calls = []

    def discover(self, country, categories=None, query=None, limit=10):
        self.calls.append((country, categories, query, limit))
        return {
            "opportunities": [
                {
                    "title": "Live Tender",
                    "organization": "World Bank Group",
                    "country": country,
                    "category": "procurement",
                    "deadline": "2026-09-30T00:00:00Z",
                    "intelligence_score": 8.5,
                }
            ],
            "recommendation": {"recommendation": "apply"},
            "explanation": {"summary": "Good match."},
            "query": {
                "country": country,
                "categories": categories or [],
                "query": query or "",
                "limit": limit,
            },
            "sources": [
                {
                    "id": "world-bank",
                    "reliability": "official",
                    "status": "live",
                }
            ],
        }


def make_request(api, payload):
    messages = []
    sent = False
    raw = json.dumps(payload).encode()

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": raw, "more_body": False}

    async def send(message):
        messages.append(message)

    asyncio.run(
        api(
            {
                "type": "http",
                "method": "POST",
                "path": "/v1/discover",
                "headers": [],
            },
            receive,
            send,
        )
    )
    return messages


def test_discover_is_public_and_delegates():
    discovery = FakeDiscoveryService()
    api = OpenRadarAPI(discovery_service=discovery)

    messages = make_request(
        api,
        {
            "country": "Nigeria",
            "categories": ["procurement"],
            "query": "digital",
            "limit": 5,
        },
    )

    assert messages[0]["status"] == 200
    payload = json.loads(messages[-1]["body"].decode())
    assert payload["opportunities"][0]["title"] == "Live Tender"
    assert discovery.calls == [
        ("Nigeria", ["procurement"], "digital", 5)
    ]


def test_discover_rejects_unsupported_category():
    api = OpenRadarAPI(discovery_service=FakeDiscoveryService())

    messages = make_request(
        api,
        {
            "country": "Nigeria",
            "categories": ["not-a-real-category"],
        },
    )

    assert messages[0]["status"] == 400
    payload = json.loads(messages[-1]["body"].decode())
    assert payload == {
        "error": "unsupported_category",
        "category": "not-a-real-category",
    }


def test_discover_rejects_non_list_categories():
    api = OpenRadarAPI(discovery_service=FakeDiscoveryService())

    messages = make_request(
        api,
        {
            "country": "Nigeria",
            "categories": "procurement",
        },
    )

    assert messages[0]["status"] == 400
    payload = json.loads(messages[-1]["body"].decode())
    assert payload == {"error": "categories_must_be_list"}
