from open_radar.opportunity_http_transport import (
    OpportunityHttpTransport,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, error=None):
        self.status_code = status_code
        self.payload = payload
        self.error = error

    def json(self):
        if self.error:
            raise self.error

        return self.payload


class FakeClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def get(self, url):
        self.calls.append(url)

        if self.error:
            raise self.error

        return self.response


def test_http_transport_fetches_list():
    client = FakeClient(
        response=FakeResponse(
            status_code=200,
            payload=[
                {"name": "Grant A"},
                {"name": "Grant B"},
            ],
        )
    )

    transport = OpportunityHttpTransport(client)

    result = transport.fetch(
        "https://example.org/opportunities"
    )

    assert result == [
        {"name": "Grant A"},
        {"name": "Grant B"},
    ]

    assert client.calls == [
        "https://example.org/opportunities"
    ]


def test_http_transport_rejects_non_200_response():
    client = FakeClient(
        response=FakeResponse(
            status_code=404,
            payload=[
                {"name": "Grant A"},
            ],
        )
    )

    transport = OpportunityHttpTransport(client)

    assert transport.fetch(
        "https://example.org/opportunities"
    ) == []


def test_http_transport_handles_network_failure():
    client = FakeClient(
        error=RuntimeError("network failure")
    )

    transport = OpportunityHttpTransport(client)

    assert transport.fetch(
        "https://example.org/opportunities"
    ) == []


def test_http_transport_handles_invalid_json():
    client = FakeClient(
        response=FakeResponse(
            status_code=200,
            error=ValueError("invalid json"),
        )
    )

    transport = OpportunityHttpTransport(client)

    assert transport.fetch(
        "https://example.org/opportunities"
    ) == []


def test_http_transport_rejects_non_list_payload():
    client = FakeClient(
        response=FakeResponse(
            status_code=200,
            payload={
                "results": [
                    {"name": "Grant A"},
                ]
            },
        )
    )

    transport = OpportunityHttpTransport(client)

    assert transport.fetch(
        "https://example.org/opportunities"
    ) == []


def test_http_transport_filters_invalid_items():
    client = FakeClient(
        response=FakeResponse(
            status_code=200,
            payload=[
                {"name": "Grant A"},
                None,
                "invalid",
                {"name": "Grant B"},
            ],
        )
    )

    transport = OpportunityHttpTransport(client)

    assert transport.fetch(
        "https://example.org/opportunities"
    ) == [
        {"name": "Grant A"},
        {"name": "Grant B"},
    ]


def test_http_transport_does_not_mutate_response_data():
    payload = [
        {"name": "Grant A"},
    ]

    client = FakeClient(
        response=FakeResponse(
            status_code=200,
            payload=payload,
        )
    )

    transport = OpportunityHttpTransport(client)

    transport.fetch(
        "https://example.org/opportunities"
    )

    assert payload == [
        {"name": "Grant A"},
    ]
