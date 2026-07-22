from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()


def runtime_url() -> str:
    return (os.environ.get("URIRUN_RUNTIME_URL") or "http://127.0.0.1:8765").rstrip("/")


def llm_api_base() -> str:
    return (
        os.environ.get("URIRUN_LLM_API_BASE")
        or os.environ.get("OPENAI_API_BASE")
        or os.environ.get("OPENROUTER_BASE_URL")
        or "https://llm.urirun.com/api/v1"
    ).rstrip("/")


def fetch_routes() -> list[dict[str, Any]]:
    for path in ("/routes", "/api/routes"):
        try:
            resp = requests.get(runtime_url() + path, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            routes = data.get("routes", data)
            if isinstance(routes, dict):
                routes = list(routes.values())
            if isinstance(routes, list):
                return [r for r in routes if isinstance(r, dict) and r.get("uri")]
        except Exception:
            continue
    return []


def agent_card() -> dict[str, Any]:
    skills = []
    for route in fetch_routes():
        uri = str(route.get("uri") or "")
        skills.append({
            "id": uri.replace("://", "_").replace("/", "_")[:96],
            "name": route.get("title") or uri,
            "description": route.get("description") or f"urirun route {uri}",
            "examples": [uri],
            "inputSchema": route.get("inputSchema") or {"type": "object", "properties": {}},
            "tags": [uri.split("://", 1)[0]],
        })
    host = os.environ.get("URIRUN_API_A2A_PUBLIC_URL") or f"http://{os.environ.get('URIRUN_API_A2A_HOST', '127.0.0.1')}:{os.environ.get('URIRUN_API_A2A_PORT', '8091')}"
    return {
        "name": "urirun-api-a2a",
        "description": "A2A gateway over urirun runtime registry",
        "url": host,
        "version": "0.1.0",
        "capabilities": {"streaming": False, "pushNotifications": False},
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json"],
        "provider": {"organization": "urirun", "llm_api_base": llm_api_base()},
        "skills": skills,
    }


def run_uri(uri: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = {"uri": uri, "mode": "execute", "payload": payload or {}}
    resp = requests.post(runtime_url() + "/run", json=body, timeout=60)
    resp.raise_for_status()
    return resp.json()


class A2ARequestHandler(BaseHTTPRequestHandler):
    server_version = "urirun-api-a2a/0.1.0"

    def _json(self, code: int, body: dict[str, Any]) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/.well-known/agent.json":
            self._json(200, agent_card())
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/invoke":
            self._json(404, {"ok": False, "error": "not found"})
            return
        size = int(self.headers.get("Content-Length", "0") or "0")
        body = json.loads(self.rfile.read(size) or b"{}")
        uri = str(body.get("uri") or "")
        if not uri:
            self._json(400, {"ok": False, "error": "uri required"})
            return
        self._json(200, run_uri(uri, body.get("payload") or {}))


def main() -> int:
    host = os.environ.get("URIRUN_API_A2A_HOST") or "0.0.0.0"
    port = int(os.environ.get("URIRUN_API_A2A_PORT") or "8091")
    server = ThreadingHTTPServer((host, port), A2ARequestHandler)
    print(f"urirun-api-a2a listening on http://{host}:{port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
