import asyncio
import json

from open_radar.api import OpenRadarAPI


TEST_API_KEY = "test-open-radar-key"


class FakeService:
    def __init__(self, should_fail=False):
        self.calls = []
        self.should_fail = should_fail

    def analyze_raw(self, opportunities, country):
        self.calls.append((opportunities, country))

        if self.should_fail:
            raise RuntimeError("failure")

        return {
            "results": [
                {
                    "title": "AI Grant",
                    "score": 92.5,
                }
            ]
        }


def make_scope(
    method="POST",
    path="/v1/analyze",
    api_key=TEST_API_KEY,
):
    headers = []

    if api_key is not None:
        headers.append(
            [
                b"x-api-key",
                api_key.encode("utf-8"),
            ]
        )

    return {
        "type": "http",
        "method": method,
        "path": path,
        "headers": headers,
    }


def run_api(
    api,
    scope,
    body=b"",
    chunks=None,
):
    messages = []

    if chunks is None:
        chunks = [body]

    index = 0

    async def receive():
        nonlocal index

        if index >= len(chunks):
            return {
                "type": "http.request",
                "body": b"",
                "more_body": False,
            }

        chunk = chunks[index]
        index += 1

        return {
            "type": "http.request",
            "body": chunk,
            "more_body": index < len(chunks),
        }

    async def send(message):
        messages.append(message)

    asyncio.run(
        api(
            scope,
            receive,
            send,
        )
    )

    return messages


def response_body(messages):
    return json.loads(
        messages[-1]["body"].decode("utf-8")
    )


def test_missing_api_key_is_rejected():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(api_key=None),
        b'{"country":"Nigeria","opportunities":[]}',
    )

    assert messages[0]["status"] == 401
    assert response_body(messages) == {
        "error": "unauthorized",
    }


def test_invalid_api_key_is_rejected():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(api_key="wrong-key"),
        b'{"country":"Nigeria","opportunities":[]}',
    )

    assert messages[0]["status"] == 401
    assert response_body(messages) == {
        "error": "unauthorized",
    }


def test_valid_api_key_is_accepted():
    service = FakeService()

    api = OpenRadarAPI(
        service=service,
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(),
        b'{"country":"Nigeria","opportunities":[]}',
    )

    assert messages[0]["status"] == 200
    assert service.calls == [
        ([], "Nigeria"),
    ]


def test_invalid_json_is_rejected():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(),
        b"{invalid",
    )

    assert messages[0]["status"] == 400
    assert response_body(messages) == {
        "error": "invalid_json",
    }


def test_non_object_json_is_rejected():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(),
        b'["not","an","object"]',
    )

    assert messages[0]["status"] == 400
    assert response_body(messages) == {
        "error": "request_body_must_be_object",
    }


def test_missing_opportunities_is_rejected():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(),
        b'{"country":"Nigeria"}',
    )

    assert messages[0]["status"] == 400
    assert response_body(messages) == {
        "error": "opportunities_must_be_list",
    }


def test_invalid_opportunities_type_is_rejected():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(),
        b'{"country":"Nigeria","opportunities":"bad"}',
    )

    assert messages[0]["status"] == 400
    assert response_body(messages) == {
        "error": "opportunities_must_be_list",
    }


def test_missing_country_is_rejected():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(),
        b'{"opportunities":[]}',
    )

    assert messages[0]["status"] == 400
    assert response_body(messages) == {
        "error": "country_required",
    }


def test_empty_country_is_rejected():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(),
        b'{"country":"   ","opportunities":[]}',
    )

    assert messages[0]["status"] == 400
    assert response_body(messages) == {
        "error": "country_required",
    }


def test_country_is_trimmed():
    service = FakeService()

    api = OpenRadarAPI(
        service=service,
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(),
        b'{"country":"  Nigeria  ","opportunities":[]}',
    )

    assert messages[0]["status"] == 200
    assert service.calls == [
        ([], "Nigeria"),
    ]


def test_service_failure_returns_500():
    api = OpenRadarAPI(
        service=FakeService(should_fail=True),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(),
        b'{"country":"Nigeria","opportunities":[]}',
    )

    assert messages[0]["status"] == 500
    assert response_body(messages) == {
        "error": "analysis_failed",
    }


def test_health_does_not_require_api_key():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(
            method="GET",
            path="/health",
            api_key=None,
        ),
    )

    assert messages[0]["status"] == 200

    assert response_body(messages) == {
        "status": "ok",
        "service": "open-radar",
        "version": "v1",
    }


def test_v1_health_does_not_require_api_key():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(
            method="GET",
            path="/v1/health",
            api_key=None,
        ),
    )

    assert messages[0]["status"] == 200

    assert response_body(messages) == {
        "status": "ok",
        "service": "open-radar",
        "version": "v1",
    }


def test_unknown_route_is_not_found():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(
            method="GET",
            path="/v1/not-a-route",
        ),
    )

    assert messages[0]["status"] == 404

    assert response_body(messages) == {
        "error": "not_found",
    }


def test_wrong_method_is_not_found():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(
            method="PUT",
            path="/v1/analyze",
        ),
        b'{"country":"Nigeria","opportunities":[]}',
    )

    assert messages[0]["status"] == 404

    assert response_body(messages) == {
        "error": "not_found",
    }


def test_body_can_arrive_in_multiple_chunks():
    service = FakeService()

    api = OpenRadarAPI(
        service=service,
        api_key=TEST_API_KEY,
    )

    chunks = [
        b'{"country":"Nigeria",',
        b'"opportunities":[]}',
    ]

    messages = run_api(
        api,
        make_scope(),
        chunks=chunks,
    )

    assert messages[0]["status"] == 200

    assert service.calls == [
        ([], "Nigeria"),
    ]


def test_non_bytes_body_chunk_is_rejected():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(),
        chunks=[
            "this-is-not-bytes",
        ],
    )

    assert messages[0]["status"] == 400

    assert response_body(messages) == {
        "error": "invalid_json",
    }


def test_oversized_request_is_rejected():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
        max_body_size=10,
    )

    messages = run_api(
        api,
        make_scope(),
        b'{"country":"Nigeria","opportunities":[]}',
    )

    assert messages[0]["status"] == 400

    assert response_body(messages) == {
        "error": "invalid_json",
    }


def test_empty_body_is_rejected():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        make_scope(),
        b"",
    )

    assert messages[0]["status"] == 400

    assert response_body(messages) == {
        "error": "invalid_json",
    }


def test_non_http_scope_is_ignored():
    api = OpenRadarAPI(
        service=FakeService(),
        api_key=TEST_API_KEY,
    )

    messages = run_api(
        api,
        {
            "type": "websocket",
            "method": "GET",
            "path": "/health",
            "headers": [],
        },
    )

    assert messages == []
