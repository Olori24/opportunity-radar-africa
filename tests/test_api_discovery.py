import asyncio
import json

from open_radar.api import OpenRadarAPI


class FakeDiscoveryService:
    def __init__(self):
        self.calls = []

    def discover(self, country, categories=None, query=None, limit=10):
        self.calls.append((country, categories, query, limit))
        return {
            "opportunities": [],
            "recommendation": {"recommendation": "review"},
            "explanation": {"summary": "No opportunities."},
            "query": {
                "country": country,
                "categories": categories,
                "query": query,
                "limit": limit,
            },
            "sources": [],
        }


def request(payload, discovery_service):
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
            discovery_service=discovery_service,
            api_key="private-key",
        )(
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


def response_body(messages):
    return json.loads(messages[-1]["body"].decode())


def test_public_discover_accepts_product_categories():
    service = FakeDiscoveryService()
    categories = [
        "startup",
        "grant",
        "accelerator",
        "fellowship",
        "scholarship",
        "job",
        "procurement",
        "consulting",
    ]

    messages = request(
        {
            "country": "Nigeria",
            "categories": categories,
            "limit": 10,
        },
        service,
    )

    assert messages[0]["status"] == 200
    assert service.calls == [
        ("Nigeria", categories, "", 10)
    ]
    assert response_body(messages)["query"]["categories"] == categories


def test_public_discover_rejects_unknown_category():
    class RejectingDiscoveryService:
        def discover(self, country, categories=None, query=None, limit=10):
            raise ValueError("unsupported_category:unknown")

    messages = request(
        {
            "country": "Nigeria",
            "categories": ["unknown"],
        },
        RejectingDiscoveryService(),
    )

    assert messages[0]["status"] == 400
    assert response_body(messages) == {
        "error": "unsupported_category",
        "category": "unknown",
    }
