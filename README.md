# BlameBug

Automated incident triage: raw error logs arrive on a **webhook**, an **n8n** workflow can route them, an **LLM** classifies severity and proposes remediation, and a **Gradio** UI shows a **plain-text report** (readable in any theme). **Styled HTML** is available at `GET /api/reports/{id}` when you open it in a browser—typically well under a minute for typical log sizes.

**Default LLM:** [Groq](https://groq.com/) (fast, free tier for inference; OpenAI-compatible API).

## Flow

1. **Ingest** — `POST /api/webhook` with JSON `{ "logs": "...", "source": "optional", "metadata": {} }`.
2. **Automate** — n8n (or any orchestrator) forwards logs from Slack, PagerDuty, email, or your log shipper.
3. **Analyze** — Groq-compatible chat completion returns structured JSON (severity, summary, actions).
4. **Report** — Server stores HTML + text in memory; Gradio at `/` shows the **text** report; `GET /api/reports/{report_id}` returns **HTML** for viewing or saving.

## Quick start (local)

```bash
cd blamebug
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
# Edit .env: set GROQ_API_KEY from https://console.groq.com/keys
uvicorn app:app --reload --host 0.0.0.0 --port 7860
```

- UI: [http://127.0.0.1:7860](http://127.0.0.1:7860)
- Health: [http://127.0.0.1:7860/health](http://127.0.0.1:7860/health)
- Webhook: `POST http://127.0.0.1:7860/api/webhook`

Optional shared secret: set `BLAMEBUG_WEBHOOK_SECRET` and send header `X-BlameBug-Secret: <same value>`.

### Example webhook

```bash
curl -s -X POST http://127.0.0.1:7860/api/webhook \
  -H 'Content-Type: application/json' \
  -d '{"logs":"ERROR PaymentError: timeout connecting to postgres\n  at app/db.py:42","source":"curl-demo"}'
```

## n8n

1. In n8n: **Workflows → Import from File** and choose `n8n/blamebug-forward.json`.
2. Open **Forward to BlameBug** and set **URL** to your deployed app: `https://<host>/api/webhook`.
3. Activate the workflow and use the **Incoming logs** webhook URL n8n shows (POST). Map your upstream payload so `body.logs` (or the expression in the JSON body) contains the raw text.

If you use `BLAMEBUG_WEBHOOK_SECRET`, add an **HTTP Header** node or extra headers on the HTTP Request node: `X-BlameBug-Secret`.

## Hugging Face Spaces

1. Create a **Docker** Space and copy this repo (or connect Git).
2. Set **Space secrets**: `GROQ_API_KEY`, optionally `BLAMEBUG_LLM_MODEL`, `BLAMEBUG_WEBHOOK_SECRET`.
3. The `Dockerfile` runs `uvicorn` on port **7860**.

Public URL pattern: `https://USER-SPACENAME.hf.space` — use `https://USER-SPACENAME.hf.space/api/webhook` in n8n.

## Configuration

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | **Primary:** Groq API key; uses `https://api.groq.com/openai/v1` automatically |
| `OPENAI_API_KEY` | Alternative: OpenAI (or any compatible API) when `GROQ_API_KEY` is unset |
| `OPENAI_BASE_URL` | Optional; overrides base URL (e.g. Azure OpenAI). If unset and `GROQ_API_KEY` is set, Groq URL is used |
| `BLAMEBUG_LLM_MODEL` | Optional; default with Groq: `llama-3.3-70b-versatile`, with OpenAI only: `gpt-4o-mini` |
| `BLAMEBUG_WEBHOOK_SECRET` | Optional; required header for `/api/webhook` |

## Stack

Python · FastAPI · Gradio · Groq (OpenAI-compatible) · n8n (workflow JSON included) · Docker for Spaces

## License

MIT
<<<<<<< HEAD
# blamebug
# blamebug
=======
>>>>>>> 5195a45 (Add BlameBug project)
