---
title: BlameBug
emoji: 🐞
colorFrom: indigo
colorTo: gray
sdk: docker
pinned: false
---

# BlameBug

BlameBug is an incident-triage automation app that converts raw backend error logs into structured, actionable incident reports.

Instead of manually reading stack traces, assigning severity, and writing summary notes, BlameBug does this pipeline automatically:

1. Receive logs via webhook
2. Analyze them with an LLM
3. Classify severity and extract impact/root-cause hypothesis
4. Produce immediate + long-term remediation actions
5. Publish a report in Gradio and as standalone HTML

Default provider is Groq (OpenAI-compatible API).

---

## What This Project Solves

During incidents, teams often spend 15-30 minutes on repetitive triage:

- Parse noisy logs
- Guess severity
- Draft a concise summary
- Write remediation steps

BlameBug compresses that into a few seconds with consistent output formatting.

---

## Architecture

### Components

- FastAPI API server (`blamebug/server.py`)
- LLM analyzer (`blamebug/analyzer.py`)
- HTML + text report builders (`blamebug/report_html.py`)
- In-memory report store (`blamebug/store.py`)
- Gradio interface mounted on FastAPI root (`/`)
- n8n forwarding workflow (`n8n/blamebug-forward.json`)

### High-level workflow

```text
Upstream Alert Source
   (Slack / PagerDuty / logs / manual test)
                |
                v
          n8n Webhook
                |
                v
      n8n HTTP Request Node
   POST /api/webhook (BlameBug)
                |
                v
        LLM Structured Analysis
                |
                v
   Store report (memory, with report_id)
                |
        +-------+------------------+
        |                          |
        v                          v
   Gradio UI (/)        HTML endpoint (/api/reports/{id})
```

---

## API Endpoints

### Health

- `GET /health`
- Returns:
  - `status`
  - `llm_configured` (true if API key is configured)

### Webhook Ingest

- `POST /api/webhook`
- JSON body:

```json
{
  "logs": "raw error text",
  "source": "optional source name",
  "metadata": {
    "env": "prod"
  }
}
```

- Success response:

```json
{
  "report_id": "uuid",
  "severity": "high",
  "processing_seconds": 1.23,
  "ok": true
}
```

### Report View

- `GET /api/reports/{report_id}`
- Returns full styled HTML report.

---

## Local Run

```bash
cd blamebug
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
# edit .env and set GROQ_API_KEY
uvicorn app:app --host 0.0.0.0 --port 7860
```

Open:

- UI: [http://127.0.0.1:7860](http://127.0.0.1:7860)
- Health: [http://127.0.0.1:7860/health](http://127.0.0.1:7860/health)

---

## Configuration

| Variable | Required | Purpose |
|---|---:|---|
| `GROQ_API_KEY` | Yes (recommended) | Primary LLM key (Groq endpoint auto-selected) |
| `OPENAI_API_KEY` | Optional | Use OpenAI/compatible provider when Groq key not set |
| `OPENAI_BASE_URL` | Optional | Override API base URL for OpenAI-compatible providers |
| `BLAMEBUG_LLM_MODEL` | Optional | Override default model |
| `BLAMEBUG_WEBHOOK_SECRET` | Optional | If set, requires `X-BlameBug-Secret` header on `/api/webhook` |

> Important: Never commit real secrets. Keep real keys in `.env` (ignored by `.gitignore`) or platform secrets.

---

## n8n Setup (Step-by-step)

### 1) Import workflow

In n8n:

- Workflows -> Import from file
- Select: `n8n/blamebug-forward.json`

This creates two nodes:

- `Incoming logs` (Webhook trigger)
- `Forward to BlameBug` (HTTP Request)

### 2) Set BlameBug target URL

Open `Forward to BlameBug` node and set:

- URL: `https://<your-host>/api/webhook`

Examples:

- Local (same machine): `http://localhost:7860/api/webhook`
- Hugging Face Space: `https://<space>.hf.space/api/webhook`

### 3) Headers

Always send:

- `Content-Type: application/json`

If `BLAMEBUG_WEBHOOK_SECRET` is enabled in BlameBug, also add:

- `X-BlameBug-Secret: <your-secret>`

### 4) Activate workflow

- Click Publish / Activate in n8n

### 5) Trigger test event

Use the `Incoming logs` webhook URL and send:

```bash
curl -s -X POST "<N8N_WEBHOOK_URL>" \
  -H "Content-Type: application/json" \
  -d '{"logs":"ERROR: db connection refused","source":"n8n-test","metadata":{"env":"prod"}}'
```

### 6) Verify execution

In n8n Executions:

- `Incoming logs` should be successful
- `Forward to BlameBug` should return HTTP 200 and include `report_id`

Then open:

- `https://<your-host>/api/reports/<report_id>`

---

## Hugging Face Spaces Deployment (Docker)

### 1) Create Space

- Create new Space
- SDK: Docker
- Visibility: Public/Private as needed

### 2) Push code to Space repo

If you already have your code in GitHub, you can either connect repo from HF UI or push directly to HF Space git remote.

### 3) Add secrets in Space Settings

- `GROQ_API_KEY`
- optional `BLAMEBUG_WEBHOOK_SECRET`

### 4) Build + run

- Wait for Space status -> Running
- Test:
  - `https://<space>.hf.space/health`
  - should return `llm_configured: true`

### 5) Connect n8n

Use this URL in n8n HTTP node:

- `https://<space>.hf.space/api/webhook`

---

## Report Behavior

- Main app (`/`) shows the latest report via Gradio
- API endpoint (`/api/reports/{id}`) returns standalone colorful HTML
- Reports are stored **in-memory** (not persisted): restarts clear history

---

## Troubleshooting

### 503 on `/api/webhook`

Cause: missing LLM key  
Fix: set `GROQ_API_KEY` or `OPENAI_API_KEY`

### 401 on `/api/webhook`

Cause: secret header mismatch  
Fix: set matching `X-BlameBug-Secret` in client/n8n

### n8n HTTP node says no input

Cause: webhook trigger node not executed first  
Fix: execute workflow and send payload to `Incoming logs` webhook URL

### HF Space shows README config error

Cause: missing/invalid YAML front-matter in README  
Fix: keep valid front-matter block at top (already included in this file)

---

## Tech Stack

- Python
- FastAPI
- Gradio
- Pydantic
- Groq / OpenAI-compatible APIs
- n8n
- Hugging Face Spaces (Docker)

---

## License

MIT
