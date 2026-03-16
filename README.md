# Vitruvius

**Architect Site Visit Report Generator** — Upload site visit photos in bulk, let AI analyze and group them, review findings interactively, and generate a professional report using your template.

## How It Works

1. **Upload** — Drop your site visit photos and an optional report template (.docx or .pdf)
2. **AI Analysis** — An agentic pipeline analyzes each photo, groups related issues, and writes professional findings
3. **Review** — Edit findings, swap photos between groups, re-prompt the AI, and approve everything line by line
4. **Generate** — Download a filled report (.docx), organized photos, and raw analysis data as a ZIP

## Architecture

```
Frontend (React + Vite + Tailwind)
    ↕  REST API + SSE
Backend (FastAPI, Python 3.11+)
    ↕  OpenRouter API
AI Models (configurable: Gemini, Claude, GPT-4o, etc.)
```

### Agentic Pipeline

| Stage | Agent | Model Type | Purpose |
|-------|-------|-----------|---------|
| 1 | Photo Analyzer | Vision | Analyze each photo individually for defects/issues |
| 2 | Photo Grouper | Text | Cluster related photos, select key representatives |
| 3 | Analysis Writer | Vision | Write professional findings per group |
| 4 | Template Analyzer | Vision/Text | Understand template structure for report generation |

Stages 1-3 run sequentially; Stage 4 runs in parallel with 1-3.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [OpenRouter](https://openrouter.ai) API key

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your OpenRouter API key

# Run
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and proxies API calls to the backend at `http://localhost:8000`.

## Configuration

All configuration is via environment variables (or `.env` file in `backend/`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | (required) | Your OpenRouter API key |
| `VISION_MODEL` | `google/gemini-2.0-flash-001` | Model for photo analysis |
| `TEXT_MODEL` | `google/gemini-2.0-flash-001` | Model for text tasks |
| `MAX_CONCURRENT_LLM_CALLS` | `5` | Parallel API call limit |
| `SESSION_TTL_SECONDS` | `3600` | Session expiry (seconds) |

Models can also be selected per-session from the upload UI.

## Project Structure

```
backend/
├── main.py              # FastAPI app entry
├── config.py            # Pydantic Settings
├── agents/              # LLM-backed agents (one per pipeline stage)
├── models/schemas.py    # All Pydantic data models
├── services/            # Business logic (LLM client, pipeline, report gen)
└── routers/             # API endpoints (upload, analysis, review, generate)

frontend/
├── src/
│   ├── api/client.ts    # Typed API client
│   ├── stores/          # Zustand state management
│   ├── components/      # React UI components
│   └── types/           # TypeScript interfaces
```

## No Storage Costs

Everything is ephemeral — sessions live in memory and auto-expire. Nothing is persisted to disk or a database. Download your report and data before the session expires.

## License

MIT
