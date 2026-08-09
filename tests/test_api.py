import asyncio
import json

from open_radar.api import OpenRadarAPI


TEST_API_KEY = "test-open-radar-key"


class FakeService:
    def __init__(self):
        self.calls = []

    def analyze_raw(self, opportunities, country):
        self.calls.append(
            (opportunities, country)
        )

        return {
            "results": [
                {
                    "title": "AI Grant",
                    "score": 92.5,
                }
            ]
        }


def request(
    method,
    path,
    payload=None,
    api_key=TEST_API_KEY,
):
    messages = []
    sent = False

    if payload is None:
        body = b""
    else:
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

    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    headers = []

    if api_key is not None:
        headers.append(
            [
                b"x-api-key",
                api_key.encode("utf-8"),
            ]
        )

    asyncio.run(
        api(
            {
                "type": "http",
                "method": method,
                "path": path,
                "headers": headers,
            },
            receive,
            send,
        )
    )

    return messages


def body(messages):
    return json.loads(
        messages[-1]["body"].decode()
    )


def test_health():
    response = request(
        "GET",
        "/health",
    )

    assert response[0]["status"] == 200

    assert body(response) == {
        "status": "ok",
        "service": "open-radar",
        "version": "v1",
    }


def test_v1_health():
    response = request(
        "GET",
        "/v1/health",
    )

    assert response[0]["status"] == 200

    assert body(response) == {
        "status": "ok",
        "service": "open-radar",
        "version": "v1",
    }


def test_unknown_route():
    response = request(
        "GET",
        "/does-not-exist",
    )

    assert response[0]["status"] == 404

    assert body(response)["error"] == "not_found"


def test_analyze_requires_opportunities():
    response = request(
        "POST",
        "/analyze",
        {
            "country": "Nigeria",
        },
    )

    assert response[0]["status"] == 400

    assert body(response)["error"] == (
        "opportunities_must_be_list"
    )


def test_analyze_requires_country():
    response = request(
        "POST",
        "/analyze",
        {
            "opportunities": [],
        },
    )

    assert response[0]["status"] == 400

    assert body(response)["error"] == (
        "country_required"
    )


def test_analyze_rejects_invalid_json():
    messages = []
    sent = False

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
            "body": b"{invalid",
            "more_body": False,
        }

    async def send(message):
        messages.append(message)

    asyncio.run(
        OpenRadarAPI(
            api_key=TEST_API_KEY,
        )(
            {
                "type": "http",
                "method": "POST",
                "path": "/analyze",
                "headers": [
                    [
                        b"x-api-key",
                        TEST_API_KEY.encode("utf-8"),
                    ]
                ],
            },
            receive,
            send,
        )
    )

    assert messages[0]["status"] == 400


def test_analyze_calls_service():
    service = FakeService()

    api = OpenRadarAPI(
        service=service,
        api_key=TEST_API_KEY,
    )

    messages = []
    sent = False

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
            "body": json.dumps(
                {
                    "country": "Nigeria",
                    "opportunities": [
                        {
                            "title": "AI Grant",
                        }
                    ],
                }
            ).encode(),
            "more_body": False,
        }

    async def send(message):
        messages.append(message)

    asyncio.run(
        api(
            {
                "type": "http",
                "method": "POST",
                "path": "/analyze",
                "headers": [
                    [
                        b"x-api-key",
                        TEST_API_KEY.encode("utf-8"),
                    ]
                ],
            },
            receive,
            send,
        )
    )

    assert messages[0]["status"] == 200

    assert service.calls == [
        (
            [{"title": "AI Grant"}],
            "Nigeria",
        )
    ]

    assert body(messages) == {
        "results": [
            {
                "title": "AI Grant",
                "score": 92.5,
            }
        ]
    }


def test_v1_analyze_calls_service():
    service = FakeService()

    api = OpenRadarAPI(
        service=service,
        api_key=TEST_API_KEY,
    )

    messages = []
    sent = False

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
            "body": json.dumps(
                {
                    "country": "Nigeria",
                    "opportunities": [
                        {
                            "title": "AI Grant",
                        }
                    ],
                }
            ).encode(),
            "more_body": False,
        }

    async def send(message):
        messages.append(message)

    asyncio.run(
        api(
            {
                "type": "http",
                "method": "POST",
                "path": "/v1/analyze",
                "headers": [
                    [
                        b"x-api-key",
                        TEST_API_KEY.encode("utf-8"),
                    ]
                ],
            },
            receive,
            send,
        )
    )

    assert messages[0]["status"] == 200

    assert service.calls == [
        (
            [{"title": "AI Grant"}],
            "Nigeria",
        )
    ]

    assert body(messages) == {
        "results": [
            {
                "title": "AI Grant",
                "score": 92.5,
            }
        ]
    }


def test_analyze_rejects_missing_api_key():
    response = request(
        "POST",
        "/analyze",
        {
            "country": "Nigeria",
            "opportunities": [],
        },
        api_key=None,
    )

    assert response[0]["status"] == 401

    assert body(response) == {
        "error": "unauthorized",
    }


def test_analyze_rejects_invalid_api_key():
    response = request(
        "POST",
        "/analyze",
        {
            "country": "Nigeria",
            "opportunities": [],
        },
        api_key="wrong-key",
    )

    assert response[0]["status"] == 401

    assert body(response) == {
        "error": "unauthorized",
    }


def test_health_does_not_require_api_key():
    response = request(
        "GET",
        "/health",
        api_key=None,
    )

    assert response[0]["status"] == 200

    assert body(response)["status"] == "ok"
