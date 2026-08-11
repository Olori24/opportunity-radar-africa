import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from open_radar.api import app as radar_app


async def app(scope, receive, send):
    if scope.get("type") == "http" and scope.get("method") == "GET" and scope.get("path") in ("/", "/live"):
        try:
            html = (ROOT / "index.html").read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            html = "<!doctype html><html><body><h1>Open Radar Africa</h1><p>Demo frontend unavailable.</p></body></html>"
        body = html.encode("utf-8")
        await send({"type":"http.response.start","status":200,"headers":[[b"content-type",b"text/html; charset=utf-8"],[b"cache-control",b"no-store"]]})
        await send({"type":"http.response.body","body":body})
        return
    await radar_app(scope, receive, send)
