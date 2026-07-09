# urirun-api-a2a

Thin A2A adapter for `urirun`.

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
python -m urirun_api_a2a.server
```

Endpoints:

- `GET /.well-known/agent.json`
- `POST /invoke`
