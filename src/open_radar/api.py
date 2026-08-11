import json
import os

from open_radar.opportunity_discovery_service import OpportunityDiscoveryService
from open_radar.opportunity_radar_service import OpportunityRadarService


class OpenRadarAPI:
    """
    Lightweight ASGI API boundary for Open Radar.

    Security principles:
    - API authentication protects production analysis endpoints.
    - Live discovery is public but tightly bounded.
    - The demo endpoint is deliberately limited and accepts no source URLs.
    - Health checks remain public.
    - Request bodies are size-limited.
    - Invalid input is rejected before reaching the service.
    - Internal exceptions are not exposed to clients.
    """

    MAX_BODY_SIZE = 1_000_000
    DEMO_MAX_BODY_SIZE = 200_000
    DEMO_MAX_OPPORTUNITIES = 25
    DISCOVER_MAX_BODY_SIZE = 20_000

    def __init__(
        self,
        service=None,
        api_key=None,
        max_body_size=None,
        discovery_service=None,
    ):
        self.service = service or OpportunityRadarService()
        self.discovery_service = discovery_service or OpportunityDiscoveryService()

        self.api_key = (
            api_key
            if api_key is not None
            else os.getenv("OPEN_RADAR_API_KEY")
        )

        self.max_body_size = (
            max_body_size
            if max_body_size is not None
            else self.MAX_BODY_SIZE
        )

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return

        method = scope.get("method", "GET")
        path = scope.get("path", "/")

        if method == "GET" and path in (
            "/health",
            "/v1/health",
        ):
            await self._json(
                send,
                200,
                {
                    "status": "ok",
                    "service": "open-radar",
                    "version": "v1",
                },
            )
            return

        if method == "POST" and path in (
            "/demo/analyze",
            "/v1/demo/analyze",
        ):
            await self._demo_analyze(receive, send)
            return

        if method == "POST" and path in (
            "/discover",
            "/v1/discover",
        ):
            await self._discover(receive, send)
            return

        if method == "POST" and path in (
            "/analyze",
            "/v1/analyze",
        ):
            if not self._authorized(scope):
                await self._json(
                    send,
                    401,
                    {
                        "error": "unauthorized",
                    },
                )
                return

            await self._analyze(receive, send)
            return

        await self._json(
            send,
            404,
            {
                "error": "not_found",
            },
        )

    def _authorized(self, scope):
        """Validate the X-API-Key header."""
        if not self.api_key:
            return False

        headers = dict(scope.get("headers", []))
        supplied_key = headers.get(b"x-api-key", b"")

        if not isinstance(supplied_key, bytes):
            return False

        try:
            supplied_key = supplied_key.decode("utf-8")
        except UnicodeDecodeError:
            return False

        return supplied_key == self.api_key

    async def _analyze(self, receive, send):
        body = await self._read_body(receive)

        if body is None:
            await self._json(send, 400, {"error": "invalid_json"})
            return

        await self._run_analysis(body, send)

    async def _demo_analyze(self, receive, send):
        body = await self._read_body(
            receive,
            max_body_size=self.DEMO_MAX_BODY_SIZE,
        )

        if body is None:
            await self._json(send, 400, {"error": "invalid_json"})
            return

        if not isinstance(body, dict):
            await self._json(
                send,
                400,
                {"error": "request_body_must_be_object"},
            )
            return

        opportunities = body.get("opportunities")
        if not isinstance(opportunities, list):
            await self._json(
                send,
                400,
                {"error": "opportunities_must_be_list"},
            )
            return

        if len(opportunities) > self.DEMO_MAX_OPPORTUNITIES:
            await self._json(
                send,
                400,
                {
                    "error": "demo_opportunity_limit_exceeded",
                    "max_opportunities": self.DEMO_MAX_OPPORTUNITIES,
                },
            )
            return

        await self._run_analysis(body, send)

    async def _discover(self, receive, send):
        body = await self._read_body(
            receive,
            max_body_size=self.DISCOVER_MAX_BODY_SIZE,
        )

        if body is None:
            await self._json(send, 400, {"error": "invalid_json"})
            return

        if not isinstance(body, dict):
            await self._json(
                send,
                400,
                {"error": "request_body_must_be_object"},
            )
            return

        country = body.get("country")
        categories = body.get("categories", [])
        query = body.get("query", "")
        limit = body.get("limit", 10)

        if not isinstance(country, str) or not country.strip():
            await self._json(send, 400, {"error": "country_required"})
            return

        if not isinstance(categories, list):
            await self._json(
                send,
                400,
                {"error": "categories_must_be_list"},
            )
            return

        if not isinstance(query, str):
            await self._json(
                send,
                400,
                {"error": "query_must_be_string"},
            )
            return

        if not isinstance(limit, int) or isinstance(limit, bool):
            await self._json(send, 400, {"error": "limit_must_be_integer"})
            return

        try:
            result = self.discovery_service.discover(
                country=country,
                categories=categories,
                query=query,
                limit=limit,
            )
        except ValueError as exc:
            message = str(exc)
            if message.startswith("unsupported_category:"):
                await self._json(
                    send,
                    400,
                    {
                        "error": "unsupported_category",
                        "category": message.split(":", 1)[1],
                    },
                )
                return

            await self._json(
                send,
                400,
                {"error": message},
            )
            return
        except Exception:
            await self._json(
                send,
                502,
                {"error": "discovery_failed"},
            )
            return

        await self._json(send, 200, result)

    async def _run_analysis(self, body, send):
        if not isinstance(body, dict):
            await self._json(
                send,
                400,
                {"error": "request_body_must_be_object"},
            )
            return

        opportunities = body.get("opportunities")
        country = body.get("country")

        if not isinstance(opportunities, list):
            await self._json(
                send,
                400,
                {"error": "opportunities_must_be_list"},
            )
            return

        if not isinstance(country, str):
            await self._json(send, 400, {"error": "country_required"})
            return

        country = country.strip()
        if not country:
            await self._json(send, 400, {"error": "country_required"})
            return

        try:
            result = self.service.analyze_raw(
                opportunities,
                country,
            )
        except Exception:
            await self._json(send, 500, {"error": "analysis_failed"})
            return

        await self._json(send, 200, result)

    async def _read_body(self, receive, max_body_size=None):
        chunks = []
        total_size = 0
        limit = (
            max_body_size
            if max_body_size is not None
            else self.max_body_size
        )

        while True:
            message = await receive()

            if message.get("type") != "http.request":
                continue

            chunk = message.get("body", b"")
            if not isinstance(chunk, bytes):
                return None

            total_size += len(chunk)
            if total_size > limit:
                return None

            chunks.append(chunk)

            if not message.get("more_body", False):
                break

        raw = b"".join(chunks)
        if not raw:
            return None

        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

    async def _json(self, send, status, payload):
        body = json.dumps(payload).encode("utf-8")

        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [[b"content-type", b"application/json"]],
            }
        )

        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )


app = OpenRadarAPI()
