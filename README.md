---
title: FaultLine
emoji: 🐞
colorFrom: indigo
colorTo: gray
sdk: docker
pinned: false
---

<div align="center">

<img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/Gradio-4.x-FF7C00?style=flat-square&logo=gradio&logoColor=white" />
<img src="https://img.shields.io/badge/Groq-LLM-F55036?style=flat-square" />
<img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
<img src="https://img.shields.io/github/stars/smit-6690/blamebug?style=flat-square&logo=github" />
<img src="https://img.shields.io/github/last-commit/smit-6690/blamebug?style=flat-square" />

<br/><br/>

```
███████╗ █████╗ ██╗   ██╗██╗  ████████╗██╗     ██╗███╗   ██╗███████╗
██╔════╝██╔══██╗██║   ██║██║  ╚══██╔══╝██║     ██║████╗  ██║██╔════╝
█████╗  ███████║██║   ██║██║     ██║   ██║     ██║██╔██╗ ██║█████╗  
██╔══╝  ██╔══██║██║   ██║██║     ██║   ██║     ██║██║╚██╗██║██╔══╝  
██║     ██║  ██║╚██████╔╝███████╗██║   ███████╗██║██║ ╚████║███████╗
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝   ╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝
```

### **Stop reading stack traces. Start shipping fixes.**

*FaultLine turns raw backend error logs into structured, actionable incident reports - in seconds.*

<br/>

[🚀 Quick Start](#-quick-start) · [📡 API Reference](#-api-reference) · [🔧 n8n Integration](#-n8n-integration) · [☁️ Deploy to Hugging Face Spaces](#️-deploy-to-hugging-face-spaces) · [🐛 Troubleshooting](#-troubleshooting)

</div>

---

## 🔥 What Problem Does This Solve?

During incidents, teams burn **15-30 minutes** on the same repetitive triage loop:

| Manual Triage | With FaultLine |
|:---|:---|
| 😩 Parse noisy, multi-line logs by eye | ✅ LLM extracts signal automatically |
| 😩 Guess severity based on gut feel | ✅ Consistent severity classification |
| 😩 Draft a concise incident summary | ✅ Structured report generated instantly |
| 😩 Brainstorm remediation steps | ✅ Immediate + long-term actions included |
| ⏱️ ~20 minutes | ⚡ ~3 seconds |

---


## 🏗️ Architecture

```text
Upstream Alert Source
  (Slack / PagerDuty / logs / curl)
              |
              v
        n8n Webhook
              |
              v
    n8n HTTP Request Node
  POST /api/webhook  <--- FaultLine server (FastAPI)
              |
              v
     LLM Structured Analysis
       (Groq / OpenAI-compatible)
              |
              v
   Store report in memory (report_id)
              |
       +------+-------------+
       |                    |
       v                    v
  Gradio UI (/)    HTML Report (/api/reports/{id})
```

### Components

| File | Role |
|:---|:---|
| `blamebug/server.py` | FastAPI API server + Gradio mount |
| `blamebug/analyzer.py` | LLM prompt + structured response parsing |
| `blamebug/report_html.py` | HTML + plain-text report builders |
| `blamebug/store.py` | In-memory report store (keyed by UUID) |
| `n8n/blamebug-forward.json` | Importable n8n workflow |

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/smit-6690/blamebug.git
cd blamebug

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -e .
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set your key:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

### 3. Run the server

```bash
uvicorn app:app --host 0.0.0.0 --port 7860
```

| Endpoint | URL |
|:---|:---|
| Gradio UI | http://127.0.0.1:7860 |
| Health check | http://127.0.0.1:7860/health |

### 4. Send your first log

```bash
curl -s -X POST http://localhost:7860/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "logs": "ERROR: SQLSTATE[HY000] [2002] Connection refused at db:5432",
    "source": "prod-api",
    "metadata": { "env": "production" }
  }'
```

Expected response:

```json
{
  "report_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "severity": "high",
  "processing_seconds": 1.87,
  "ok": true
}
```

Then open: `http://localhost:7860/api/reports/<report_id>`

---


## ⚙️ Configuration

| Variable | Required | Description |
|:---|:---:|:---|
| `GROQ_API_KEY` | ✅ Recommended | Primary LLM provider (free tier available) |
| `OPENAI_API_KEY` | Optional | Fallback if Groq key not set |
| `OPENAI_BASE_URL` | Optional | Override for any OpenAI-compatible endpoint |
| `FAULTLINE_LLM_MODEL` | Optional | Override default model name |
| `FAULTLINE_WEBHOOK_SECRET` | Optional | Require `X-FaultLine-Secret` header on ingest |

> ⚠️ **Never commit real secrets.** Use `.env` locally (already in `.gitignore`) or platform-level secrets in production.

---

---

## 📸 Screenshots

> **Gradio Dashboard — Latest Incident Report**

![FaultLine Gradio UI](https://raw.githubusercontent.com/smit-6690/blamebug/main/1.png)

*The main Gradio interface at `/` shows the latest parsed incident with severity badge, root-cause hypothesis, and remediation steps.*

<br/>

> **Standalone HTML Report**

![FaultLine HTML Report](https://raw.githubusercontent.com/smit-6690/blamebug/main/2.png)

*Each incident gets a fully styled, shareable HTML report accessible at `/api/reports/{report_id}`.*

<br/>

> **n8n Workflow — Log Forwarding Pipeline**

![n8n Workflow](https://raw.githubusercontent.com/smit-6690/blamebug/main/4.png)

*Two-node n8n workflow: a webhook trigger that captures upstream alerts, forwarding them directly to FaultLine's ingest endpoint.*

---
## 📡 API Reference

### `GET /health`

Returns server health and LLM configuration status.

```json
{
  "status": "ok",
  "llm_configured": true
}
```

---

### `POST /api/webhook`

Ingest raw logs for analysis.

**Request body:**

```json
{
  "logs": "raw error text or stack trace",
  "source": "optional-source-label",
  "metadata": {
    "env": "prod"
  }
}
```

**Success response:**

```json
{
  "report_id": "uuid",
  "severity": "high",
  "processing_seconds": 1.23,
  "ok": true
}
```

**Optional header** (if `FAULTLINE_WEBHOOK_SECRET` is set):

`X-FaultLine-Secret: your-secret`

---

### `GET /api/reports/{report_id}`

Returns a full, standalone styled HTML incident report.

---

## 🔧 n8n Integration

FaultLine ships with a ready-to-import n8n workflow for routing upstream alerts.

### Step-by-step setup

**1. Import the workflow**

In n8n: **Workflows -> Import from file -> select `n8n/blamebug-forward.json`**

This creates two nodes:

- `Incoming logs` - Webhook trigger
- `Forward to FaultLine` - HTTP Request

**2. Set the FaultLine target URL**

In the `Forward to FaultLine` node, set the URL to your FaultLine server:

| Environment | URL |
|:---|:---|
| Local (same machine) | `http://localhost:7860/api/webhook` |
| Hugging Face Space | `https://<space>.hf.space/api/webhook` |

**3. Configure headers**

Always include:

`Content-Type: application/json`

If using webhook secret:

`X-FaultLine-Secret: <your-secret>`

**4. Activate & test**

Click **Publish / Activate**, then trigger a test event:

```bash
curl -s -X POST "<N8N_WEBHOOK_URL>" \
  -H "Content-Type: application/json" \
  -d '{
    "logs": "ERROR: db connection refused",
    "source": "n8n-test",
    "metadata": { "env": "prod" }
  }'
```

**5. Verify in n8n Executions**

- `Incoming logs` -> ✅ Successful
- `Forward to FaultLine` -> ✅ HTTP 200 with `report_id`

---

## ☁️ Deploy to Hugging Face Spaces

### 1. Create a new Space

- SDK: **Docker**
- Visibility: Public or Private

### 2. Push code to your Space repo

Either connect your GitHub repo from the HF UI, or push directly:

```bash
git remote add hf https://huggingface.co/spaces/smit1618/blamebug-demo
git push hf main
```

### 3. Add secrets in Space Settings

| Secret | Value |
|:---|:---|
| `GROQ_API_KEY` | Your Groq API key |
| `FAULTLINE_WEBHOOK_SECRET` | *(Optional)* Ingest protection secret |

### 4. Verify deployment

Once status shows **Running**:

`https://<space>.hf.space/health`

Should return: `"llm_configured": true`

### 5. Connect n8n

Point your n8n HTTP node at:

`https://<space>.hf.space/api/webhook`

---

## 🐛 Troubleshooting

| Symptom | Cause | Fix |
|:---|:---|:---|
| `503` on `/api/webhook` | Missing LLM API key | Set `GROQ_API_KEY` or `OPENAI_API_KEY` in `.env` |
| `401` on `/api/webhook` | Secret header mismatch | Ensure `X-FaultLine-Secret` matches `FAULTLINE_WEBHOOK_SECRET` |
| n8n says "no input data" | Webhook trigger not hit first | Execute workflow, then send payload to `Incoming logs` URL |
| n8n test URL 404 (`webhook-test`) | Workflow not in test-listening state | Click **Execute workflow**, then send once; or use production `webhook` URL |
| HF Space README config error | Invalid YAML front-matter | Keep valid metadata block at top of README |

---

## 🛠️ Tech Stack

- Python
- FastAPI
- Gradio
- Pydantic
- Groq (OpenAI-compatible APIs)
- n8n
- Hugging Face Spaces (Docker)

| Layer | Technology |
|:---:|:---:|
| API Server | FastAPI |
| UI | Gradio |
| LLM | Groq (OpenAI-compatible) |
| Validation | Pydantic |
| Automation | n8n |
| Hosting | Hugging Face Spaces (Docker) |

</div>


<div align="center">

**Built to end the log-reading dark age.**

*If BlameBug saved your on-call night, drop a ⭐ — it means a lot.*

</div>
