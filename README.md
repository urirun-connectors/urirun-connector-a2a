# urirun-connector-a2a

Thin A2A connector for `urirun`.

The import path `urirun_api_a2a` and command `urirun-api-a2a` remain available for backward compatibility. New integrations should use `urirun-connector-a2a`.

It publishes an Agent Card derived from the live `urirun` runtime registry and forwards JSON invocations to `POST /run`.

## Environment

See `.env.example`.

Main variables:

- `URIRUN_RUNTIME_URL`
- `URIRUN_API_A2A_HOST`
- `URIRUN_API_A2A_PORT`
- `URIRUN_LLM_API_BASE`

## Run

```bash
cp .env.example .env
pip install -e .
urirun-connector-a2a
```

Endpoints:

- `GET /.well-known/agent.json`
- `POST /invoke`
