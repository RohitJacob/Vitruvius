<p align="center">
  <img src="assets/logo-full.png" alt="Vitruvius" width="420" />
</p>

<p align="center">
  Upload site visit photos. Get a professional inspection report.
</p>

---

## How It Works

1. **Upload** — Drop your site visit photos and an optional report template (.docx or .pdf).
2. **Analyze** — An agentic AI pipeline inspects each photo, groups related issues, and writes professional findings.
3. **Review** — Edit findings, reorganize photo groups, swap key photos, re-prompt the AI, approve line by line.
4. **Export** — Download a filled report (.docx), organized photos, and raw analysis data as a .zip.

Nothing is persisted — sessions live in memory and auto-expire. Download your report before the session ends.

## Pipeline

The analysis runs as a four-stage pipeline orchestrated by `services/pipeline.py`. Each stage updates a unified progress bar streamed to the frontend via SSE (polled every 300ms).

```
┌─────────────────────────────────────────────────────────────────────┐
│  0%                    Progress                              100%  │
│  ├── Analyze Photos ──┤── Group ──┤── Write Findings ──┤── Done ──┤│
│       (40%)              (15%)          (40%)             (5%)     │
└─────────────────────────────────────────────────────────────────────┘
```

| Stage | Agent | Model | What it does |
|-------|-------|-------|--------------|
| 1. Analyze Photos | `PhotoAnalyzerAgent` | Vision | Each photo is sent individually to a vision model. Returns description, issues, severity, location hints, and tags. Runs concurrently (up to `MAX_CONCURRENT_LLM_CALLS`). |
| 2. Group Issues | `PhotoGrouperAgent` | Text | Takes all individual analyses and clusters them by underlying issue. Selects 1–3 key representative photos per group. Single LLM call. |
| 3. Write Findings | `AnalysisWriterAgent` | Vision | For each group, sends key photos + analysis summaries to write a professional finding (observation, cause, recommendation, severity). Runs concurrently. |
| 4. Analyze Template | `TemplateAnalyzerAgent` | Vision/Text | *(optional, runs in parallel with stages 1–3)* Parses the uploaded template to understand its structure for report generation. |

Progress is weighted across stages so the bar moves smoothly throughout the entire pipeline, not per-stage.

## Architecture

```
Frontend (React 18 + Vite + TypeScript + Tailwind CSS)
    ↕  REST + SSE (progress streaming)
Backend (FastAPI + Python 3.11+)
    ↕  OpenRouter API
LLM Models (default: google/gemini-2.0-flash-001)
```

**Frontend**: Zustand for state, Axios for API calls, CSS custom properties for light/dark theming, page transitions via fade animation.

**Backend**: In-memory session management, async pipeline with `asyncio.create_task`, background task + polling SSE for real-time progress, `python-docx` / `docxtpl` for report generation.

## Quick Start

### One command

```bash
./start.sh
```

This creates a `uv` virtual environment, installs all dependencies, and starts both servers.

### Manual setup

**Backend:**

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OpenRouter API key
uvicorn main:app --reload --port 8111
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5111`. API docs at `http://localhost:8111/docs`.

## Configuration

Set these in `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | *(required)* | Your [OpenRouter](https://openrouter.ai) API key |
| `VISION_MODEL` | `google/gemini-2.0-flash-001` | Model for photo analysis and finding writing |
| `TEXT_MODEL` | `google/gemini-2.0-flash-001` | Model for grouping and text tasks |
| `MAX_CONCURRENT_LLM_CALLS` | `5` | Max parallel LLM requests |
| `SESSION_TTL_SECONDS` | `3600` | Session auto-expiry (seconds) |

## Project Structure

```
backend/
├── main.py                 # FastAPI app, CORS, lifespan
├── config.py               # Pydantic Settings from .env
├── agents/
│   ├── base.py             # Abstract agent with retry logic
│   ├── photo_analyzer.py   # Stage 1 — vision analysis per photo
│   ├── photo_grouper.py    # Stage 2 — cluster into issue groups
│   ├── analysis_writer.py  # Stage 3 — write findings per group
│   └── template_analyzer.py# Stage 4 — parse report template
├── models/schemas.py       # All Pydantic models
├── services/
│   ├── llm_client.py       # Async OpenRouter wrapper (text + vision)
│   ├── pipeline.py         # Pipeline orchestrator with weighted progress
│   ├── session_manager.py  # In-memory sessions with TTL cleanup
│   └── report_generator.py # .docx generation and .zip packaging
└── routers/
    ├── upload.py            # POST /api/upload
    ├── analysis.py          # POST /api/sessions/{id}/analyze (SSE)
    ├── review.py            # PATCH findings, move photos, re-analyze
    └── generate.py          # GET download .docx / .zip

frontend/
├── src/
│   ├── api/client.ts       # Typed API client with SSE reader
│   ├── stores/
│   │   ├── reportStore.ts  # App state (Zustand)
│   │   └── themeStore.ts   # Light/dark mode
│   ├── components/
│   │   ├── Layout.tsx       # Shell with header + theme toggle
│   │   ├── UploadPanel.tsx  # Landing page with photo/template upload
│   │   ├── ProcessingPanel.tsx # Progress bar with stage labels
│   │   ├── ReviewPanel.tsx  # Interactive finding editor
│   │   ├── GeneratePanel.tsx# Export summary + download buttons
│   │   ├── PhotoGroup.tsx   # Expandable group card
│   │   ├── PhotoCard.tsx    # Photo thumbnail with key/move actions
│   │   ├── AnalysisEditor.tsx # Inline finding editor
│   │   └── ThemeToggle.tsx  # Light/dark switch
│   └── types/index.ts      # TypeScript interfaces
```

## License

MIT
