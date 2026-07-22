from __future__ import annotations

from urirun_api_a2a import server


class Response:
    def __init__(self, data, error=False):
        self.data = data
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise RuntimeError("request failed")

    def json(self):
        return self.data


def test_fetch_routes_falls_back_and_normalizes_registry(monkeypatch):
    calls = []

    def get(url, timeout):
        calls.append((url, timeout))
        if url == "http://127.0.0.1:8765/routes":
            return Response({}, error=True)
        return Response({"routes": [{"uri": "test://one"}, {"title": "ignored"}]})

    monkeypatch.setattr(server.requests, "get", get)

    assert server.fetch_routes() == [{"uri": "test://one"}]
    assert [url for url, _ in calls] == [
        "http://127.0.0.1:8765/routes",
        "http://127.0.0.1:8765/api/routes",
    ]


def test_agent_card_projects_runtime_routes(monkeypatch):
    monkeypatch.setenv("URIRUN_API_A2A_PUBLIC_URL", "https://agents.example.test/a2a")
    monkeypatch.setattr(
        server,
        "fetch_routes",
        lambda: [
            {
                "uri": "screen://host/capture",
                "title": "Capture screen",
                "description": "Capture the current desktop",
                "inputSchema": {"type": "object", "properties": {"format": {"type": "string"}}},
            }
        ],
    )

    card = server.agent_card()

    assert card["name"] == "urirun-connector-a2a"
    assert card["url"] == "https://agents.example.test/a2a"
    assert card["skills"][0]["id"] == "screen_host_capture"
    assert card["skills"][0]["tags"] == ["screen"]


def test_run_uri_posts_the_execution_envelope(monkeypatch):
    calls = []

    def post(url, json, timeout):
        calls.append((url, json, timeout))
        return Response({"ok": True, "result": "done"})

    monkeypatch.setattr(server.requests, "post", post)

    result = server.run_uri("test://one", {"value": 2})

    assert result == {"ok": True, "result": "done"}
    assert calls == [
        (
            "http://127.0.0.1:8765/run",
            {"uri": "test://one", "mode": "execute", "payload": {"value": 2}},
            60,
        )
    ]


def test_llm_api_base_uses_documented_precedence(monkeypatch):
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.example/v1/")
    monkeypatch.setenv("OPENAI_API_BASE", "https://openai.example/v1/")
    monkeypatch.setenv("URIRUN_LLM_API_BASE", "https://urirun.example/v1/")

    assert server.llm_api_base() == "https://urirun.example/v1"
