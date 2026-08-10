import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from open_radar.api import app as open_radar_app


async def app(scope, receive, send):
    if scope.get("type") == "http" and scope.get("path") == "/v1/debug-auth":
        value = os.getenv("OPEN_RADAR_API_KEY")

        body = (
            '{"configured": %s, "length": %s}'
            % (bool(value), len(value) if value else 0)
        ).encode("utf-8")

        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        })

        await send({
            "type": "http.response.body",
            "body": body,
        })
        return

    await open_radar_app(scope, receive, send)
