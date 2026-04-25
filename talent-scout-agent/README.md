# Talent Scout Agent

> AI-powered candidate scouting, matching, and conversational engagement.
> Paste a JD → get a ranked shortlist scored on **Match × Interest**.

![Stack: FastAPI + React + Claude](https://img.shields.io/badge/stack-FastAPI%20%2B%20React%20%2B%20Claude-6366f1)

---

## What it does

This agent solves the recruiter's hardest problem: *finding the right people AND knowing if they'd actually be interested*. Most ATS tools can do one or the other. This does both.

### The 5-stage pipeline

| Stage | What happens | Tech |
|---|---|---|
| **1. JD Parsing** | LLM extracts skills, experience, seniority, domain, location into structured JSON with parsing confidence | Claude Sonnet 4.6 |
| **2. Discovery** | Searches synthetic candidate pool (60 profiles) + GitHub public API (real users) | Synthetic DB + GitHub API |
| **3. Matching & Explainability** | Hybrid scoring: deterministic for skills/exp/location (transparent) + LLM for natural-language explanation | Claude + rule engine |
| **4. Conversational Outreach** | Two LLMs converse: a recruiter LLM and a candidate LLM seeded with a hidden "interest archetype" (eager / curious / lukewarm / passive / not_interested) | Claude (multi-agent) |
| **5. Interest Scoring** | Analyzes transcript for behavioral signals (questions asked, availability shared, concerns raised, sentiment) → 0-100 Interest Score + recommended next step | Claude |

### Final output
A ranked shortlist where **Combined Score = 0.6 × Match + 0.4 × Interest**, with full explainability:
- Per-skill match badges (matched / related / missing)
- 5-axis score breakdown (skills, experience, seniority, domain, location)
- Strengths and gaps in plain English
- Full conversation transcript with archetype label
- Specific next-step recommendation per candidate
- CSV export

---

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│  React (Vite)    │────▶│  FastAPI         │────▶│  5 Agents          │
│  - JD form       │     │  - /api/scout    │     │  - JD Parser       │
│  - Progress UI   │◀────│  - /api/jobs/:id │◀────│  - Discovery       │
│  - Shortlist     │     │  - polling       │     │  - Matcher         │
│                  │     │                  │     │  - Outreach        │
└──────────────────┘     └──────────────────┘     │  - Interest Scorer │
                                                   └────────────────────┘
                                                           │
                                                ┌──────────┴──────────┐
                                                ▼                     ▼
                                        ┌─────────────┐      ┌──────────────┐
                                        │ Synthetic   │      │ GitHub API   │
                                        │ DB (60      │      │ (real users) │
                                        │ profiles)   │      │              │
                                        └─────────────┘      └──────────────┘
```

**Key design decisions:**

1. **Hybrid scoring** (deterministic + LLM) keeps Match Scores reproducible while still being explainable. Pure LLM scoring varies between runs; pure rules lack nuance.
2. **Hidden archetype** for the candidate LLM — the recruiter LLM doesn't know it. This forces the system to *infer* interest from the conversation, just like a real recruiter would.
3. **Parallel outreach** via ThreadPoolExecutor — engages 4 candidates concurrently, cutting wait time ~4x.
4. **Background jobs + polling** — no websockets needed, keeps deployment simple.

---

## Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Optional: a [GitHub personal access token](https://github.com/settings/tokens) (no scopes needed; bumps rate limits 60→5000/hr)

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env

uvicorn app.main:app --reload --port 8000
```

API is now live at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Usage

1. Paste a job description (or click a sample chip)
2. Pick how many candidates to engage (default 8)
3. Pick channel: Email / LinkedIn / SMS (changes the outreach tone)
4. Toggle GitHub source on/off
5. Click **Start Scouting**
6. Watch the 5-stage pipeline run live
7. Browse the ranked shortlist — expand any card for full details and the conversation transcript
8. Export to CSV when done

---

## Deployment

### Backend (Railway / Render / Fly.io)

The backend is a stateless FastAPI app — deploy anywhere that runs Python.

**Required env vars:**
- `GITHUB_TOKEN` (optional but recommended)
- `ALLOWED_ORIGINS` (comma-separated, set to your frontend URL)

**Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Frontend (Vercel / Netlify)

```bash
cd frontend
npm run build
# Deploy the dist/ folder
```

Set the env var `VITE_API_BASE` to your backend URL (e.g. `https://your-api.railway.app`).

### Docker (full stack)

```bash
docker compose up
```
See `docker-compose.yml` in the repo.

---

## API Reference

### `POST /api/scout`
Start a scouting job.
```json
{
  "job_description": "Senior Backend Engineer ...",
  "max_candidates_to_engage": 8,
  "include_github_search": true,
  "channels": ["email"]
}
```
Returns `{ "job_id": "job_abc123", "status_url": "/api/jobs/job_abc123" }`.

### `GET /api/jobs/{job_id}`
Poll for status. When `stage == "complete"`, the `result` field contains the full `ShortlistResponse`.

### `GET /api/health`
Health check.

Full schema in `backend/app/models/schemas.py`.

---

## Extending

- **Add real candidate sources**: implement a function in `app/agents/discovery.py` that returns `List[Candidate]`. LinkedIn, AngelList, internal ATS — same shape.
- **Tune scoring weights**: edit `app/agents/matcher.py::score_candidate` (currently 50% skills, 20% experience, 10% each of seniority/domain/location).
- **Add archetypes**: edit `ARCHETYPE_PROMPTS` in `app/agents/outreach.py`.
- **Persist jobs**: replace the in-memory `_JOBS` dict in `app/services/orchestrator.py` with Redis or Postgres.

---

## Project structure

```
talent-scout-agent/
├── backend/
│   ├── app/
│   │   ├── agents/          # 5 agents
│   │   │   ├── jd_parser.py
│   │   │   ├── discovery.py
│   │   │   ├── matcher.py
│   │   │   ├── outreach.py
│   │   │   └── interest_scorer.py
│   │   ├── data/
│   │   │   ├── synthetic_db.py
│   │   │   └── candidates.json (auto-generated on first run)
│   │   ├── models/schemas.py
│   │   ├── services/
│   │   │   ├── llm_client.py
│   │   │   └── orchestrator.py
│   │   ├── routes/scout.py
│   │   └── main.py
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── JDForm.jsx
    │   │   ├── ProgressView.jsx
    │   │   ├── CandidateCard.jsx
    │   │   └── Shortlist.jsx
    │   ├── api/client.js
    │   ├── App.jsx
    │   └── main.jsx
    ├── package.json
    └── vite.config.js
```

---

## Cost & performance

- **One full pipeline run** (8 candidates engaged) ≈ ~30-50 LLM calls (1 JD parse + 8 explanations + ~24 conversation turns + 8 interest analyses)
- **Approximate cost per run:** $0.05 - $0.15 with Claude Sonnet 4.6
- **Latency:** 30-90 seconds typical (parallelized outreach)

Switch to Claude Haiku 4.5 for ~5x cost reduction by setting `CLAUDE_MODEL=claude-haiku-4-5-20251001`.

---

## Limitations & next steps

This is a working prototype. Production-readiness gaps:

- ❌ No auth — add OAuth before deploying publicly
- ❌ In-memory job store — use Redis/Postgres for multi-instance
- ❌ Synthetic candidates only mostly — wire up real sources (LinkedIn API requires partnership; alternatives: Apollo.io, Hunter, ContactOut)
- ❌ Outreach is *simulated* — wire up SendGrid/Twilio/LinkedIn API for real sends
- ❌ No feedback loop — production should let recruiters flag wrong matches to improve scoring
- ❌ No caching — repeat runs of the same JD waste tokens

---

Built with Claude Sonnet 4.6.
