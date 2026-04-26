# Talent Scout Agent

> AI-powered candidate scouting, matching, and conversational engagement.
> Paste a JD → get a ranked shortlist scored on **Match × Interest**.

![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20React%20%2B%20Groq-6366f1)
![Python](https://img.shields.io/badge/python-3.10%2B-3776ab)
![Node](https://img.shields.io/badge/node-18%2B-339933)

---

## Overview

This agent solves the recruiter's hardest problem: *finding the right people AND knowing whether they would actually be interested*. Most ATS tools handle one or the other, not both. Talent Scout combines deterministic skill matching with conversational interest simulation so the final shortlist reflects realistic hiring outcomes rather than just keyword overlap.

The system is built on a Groq-hosted Llama 3.3 70B model for all language understanding tasks (JD parsing, conversational outreach, interest scoring, and human-readable explanations). The free tier from Groq is sufficient for ordinary use, which makes the project effectively zero-cost to run.

---

## The 5-Stage Pipeline

| Stage | What happens | Implementation |
|---|---|---|
| **1. JD Parsing** | LLM extracts skills, experience, seniority, domain, location into structured JSON with parsing confidence. Handles formal corporate JDs, casual Slack messages, Indian abbreviations (LPA / WFO / CTC), and multilingual input. | `agents/jd_parser.py` — Groq Llama 3.3 70B in JSON mode |
| **2. Discovery** | Searches the synthetic candidate pool (60 profiles across 15 role templates) and optionally the GitHub public Search API. Pre-filters by skill overlap to avoid wasting LLM tokens on poor fits. | `agents/discovery.py` — synthetic DB + GitHub API |
| **3. Matching & Explainability** | Hybrid scoring: deterministic for skills, experience, seniority, domain, and location (50 / 20 / 10 / 10 / 10 weights), plus an LLM-generated natural-language explanation with strengths and gaps. | `agents/matcher.py` — rule engine + Groq Llama |
| **4. Conversational Outreach** | Two LLMs converse over multiple turns. The recruiter LLM writes channel-aware outreach. The candidate LLM is seeded with a hidden interest archetype (eager / curious / lukewarm / passive / not_interested) drawn from a realistic weighted distribution. | `agents/outreach.py` — multi-agent simulation |
| **5. Interest Scoring** | Analyzes the transcript for behavioral signals (questions asked, availability shared, concerns raised, sentiment, engagement depth) and produces a 0–100 Interest Score plus a recommended next step. | `agents/interest_scorer.py` — Groq Llama + deterministic combiner |

### Final Output

A ranked shortlist where **Combined Score = 0.6 × Match + 0.4 × Interest**, with full explainability: per-skill match badges (matched / related / missing), a 5-axis score breakdown, plain-English strengths and gaps, the full conversation transcript with archetype label, a specific next-step recommendation, and CSV export.

---

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│  React (Vite)    │────▶│  FastAPI         │────▶│  5 Agents          │
│  - JD form       │     │  - /api/scout    │     │  - JD Parser       │
│  - Progress UI   │◀────│  - /api/jobs/:id │◀────│  - Discovery       │
│  - Shortlist     │     │  - /api/jobs     │     │  - Matcher         │
│  - CSV export    │     │  - polling       │     │  - Outreach        │
└──────────────────┘     └──────────────────┘     │  - Interest Scorer │
                                                   └────────────────────┘
                                                           │
                                          ┌────────────────┼────────────────┐
                                          ▼                ▼                ▼
                                   ┌─────────────┐  ┌──────────────┐ ┌──────────────┐
                                   │ Synthetic   │  │ GitHub API   │ │ Groq         │
                                   │ DB (60      │  │ (real users) │ │ Llama 3.3    │
                                   │ profiles)   │  │              │ │ 70B / 8B     │
                                   └─────────────┘  └──────────────┘ └──────────────┘
```

### Key Design Decisions

The hybrid scoring approach (deterministic plus LLM) keeps Match Scores reproducible across runs while still delivering plain-English explanations. Pure LLM scoring varies between runs; pure rules lack nuance, so the system uses each where it is strongest.

The candidate's interest archetype is hidden from the recruiter LLM. This forces the system to *infer* interest from the conversation, just as a real recruiter would, and prevents the simulation from short-circuiting through metadata leakage.

Outreach runs in parallel via `ThreadPoolExecutor` (default four workers), engaging top candidates concurrently and cutting wall-clock latency by roughly four times.

Background jobs use FastAPI's `BackgroundTasks` plus polling rather than WebSockets, keeping deployment simple and stateless. Job state lives in an in-memory dictionary, which is suitable for a prototype but should be replaced for production (see Limitations).

---

## Local Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- A free [Groq API key](https://console.groq.com/keys) (required)
- Optional: a [GitHub personal access token](https://github.com/settings/tokens) — no scopes needed; lifts the public-API rate limit from 60 to 5,000 requests per hour

### Option A: One-command quickstart (macOS / Linux)

The repository ships with `quickstart.sh`, which sets up the backend virtualenv, installs both backends, and starts both servers in a single terminal.

```bash
chmod +x quickstart.sh
./quickstart.sh
```

You still need to create `backend/.env` with your `GROQ_API_KEY` before running it (see below).

### Option B: Manual setup

#### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env from the template below, then edit it
cat > .env <<'EOF'
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_FAST_MODEL=llama-3.1-8b-instant
ALLOWED_ORIGINS=*
# GITHUB_TOKEN=optional_token_here
EOF

uvicorn app.main:app --reload --port 8000
```

The API is now live at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

#### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

> **Security note:** The `.env` file should never be committed to version control. If a key has ever been pushed to a public repository, rotate it in the Groq console immediately.

---

## Usage

1. Paste a job description into the form, or click one of the four sample chips (Senior Backend Python, ML Engineer LLM Apps, Casual Slack-style, or Indian-style with LPA/WFO).
2. Choose how many top candidates to engage (default 8, range 1–20).
3. Pick an outreach channel: Email, LinkedIn, or SMS. The channel changes the recruiter LLM's tone, length, and formatting (for example, Email includes a subject line; SMS stays under 280 characters).
4. Toggle the GitHub source on or off. Leaving it on adds up to five real GitHub users discovered via the public Search API.
5. Click **Start Scouting**.
6. Watch the five-stage pipeline run live, with progress updates polled every 1.5 seconds.
7. Browse the ranked shortlist. Expand any card to see the per-skill match badges, the 5-axis score breakdown, the full conversation transcript with the archetype label revealed, and the recommended next step.
8. Click **Export CSV** when done.

---

## Deployment

### Backend (Railway, Render, Fly.io, or any Python host)

The backend is a stateless FastAPI app with a Dockerfile included. Deploy anywhere that runs Python 3.10+.

**Required environment variables:**

- `GROQ_API_KEY` — required; obtain from the Groq console
- `ALLOWED_ORIGINS` — comma-separated list of allowed origins; set to your frontend URL in production
- `GROQ_MODEL` — optional; defaults to `llama-3.3-70b-versatile`
- `GROQ_FAST_MODEL` — optional; defaults to `llama-3.1-8b-instant`
- `GITHUB_TOKEN` — optional but recommended for higher rate limits

**Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Frontend (Vercel, Netlify, or any static host)

```bash
cd frontend
npm run build
# Deploy the dist/ folder
```

Set the environment variable `VITE_API_BASE` to your backend URL (for example, `https://your-api.railway.app`).

### Docker Compose (full stack)

The repository includes Dockerfiles for both services and a top-level `docker-compose.yml`.

```bash
GROQ_API_KEY=your_key_here docker compose up --build
```

The backend will be exposed on port 8000 and the Nginx-served frontend on port 8080.

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

Poll for status. Stages progress through `parsing → discovering → matching → engaging → scoring → complete` (or `failed`). When `stage == "complete"`, the `result` field contains the full `ShortlistResponse`.

### `GET /api/jobs`

List all recent jobs in memory. Useful for debugging or browsing recent runs.

### `GET /api/health`

Health check, returns `{ "status": "ok" }`.

The full Pydantic schema is defined in `backend/app/models/schemas.py`.

---

## Project Structure

```
talent-scout-agent/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── jd_parser.py
│   │   │   ├── discovery.py
│   │   │   ├── matcher.py
│   │   │   ├── outreach.py
│   │   │   └── interest_scorer.py
│   │   ├── data/
│   │   │   ├── synthetic_db.py        # 15 role templates × 4 = 60 candidates
│   │   │   └── candidates.json        # auto-generated on first run
│   │   ├── models/schemas.py
│   │   ├── services/
│   │   │   ├── llm_client.py          # Groq SDK wrapper
│   │   │   └── orchestrator.py        # 5-stage pipeline + in-memory job store
│   │   ├── routes/scout.py
│   │   └── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env                           # never commit this
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── JDForm.jsx             # JD input + sample chips + channel picker
│   │   │   ├── ProgressView.jsx
│   │   │   ├── CandidateCard.jsx
│   │   │   └── Shortlist.jsx          # ranked table + CSV export
│   │   ├── api/client.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── quickstart.sh                      # one-command local dev
└── clean.bat                          # Windows cleanup script
```

---

## Extending the System

To add a real candidate source, implement a function in `app/agents/discovery.py` that returns `List[Candidate]`. LinkedIn, AngelList, Apollo.io, or an internal ATS all use the same shape.

To tune the scoring weights, edit `app/agents/matcher.py::score_candidate`. The current weighting is 50% skills, 20% experience, and 10% each for seniority, domain, and location.

To add or modify candidate archetypes, edit `ARCHETYPE_PROMPTS` and the weighted distribution in `app/agents/outreach.py::_pick_archetype`. The current weights are eager 15%, curious 30%, lukewarm 25%, passive 20%, and not interested 10%.

To persist jobs across restarts or scale beyond a single instance, replace the in-memory `_JOBS` dict in `app/services/orchestrator.py` with Redis or Postgres.

To swap the LLM provider, modify `app/services/llm_client.py`. The agents only depend on the `complete` and `complete_json` methods, so any provider with chat completion and JSON mode will work.

---

## Cost and Performance

A full pipeline run with eight candidates engaged makes approximately 30 to 50 LLM calls — one JD parse, eight match explanations, around 24 conversation turns (recruiter and candidate alternating, with early termination for `not_interested` and `passive` archetypes), and eight interest analyses.

Using Groq's free tier with Llama 3.3 70B Versatile, this typically costs **$0.00**. Groq's free quota is generous enough for development and demonstration; for higher volumes, the paid tier is among the cheapest production-grade LLM options available.

Typical latency is 30–90 seconds per run, with parallelized outreach being the dominant factor. Switching `GROQ_MODEL` to `llama-3.1-8b-instant` reduces both latency and cost further at some loss of reasoning quality.

---

## Limitations and Next Steps

This is a working prototype. The following gaps must be addressed before any production deployment.

There is no authentication layer; OAuth or an API gateway must be added before the service is exposed publicly. The job store is in-memory, which prevents multi-instance scaling and loses state on restart — Redis or Postgres is the obvious replacement. The candidate pool is mostly synthetic; real production sourcing requires integrating LinkedIn (which needs a partnership) or alternatives such as Apollo.io, Hunter, or ContactOut. Outreach is currently *simulated* end-to-end; wiring up SendGrid for email, Twilio for SMS, and the LinkedIn API for InMail is required for real sends. There is no feedback loop, so recruiters cannot flag wrong matches to improve scoring over time. Finally, repeat runs of the same JD waste tokens because there is no caching layer.

---

## License and Acknowledgments

Built with FastAPI, React, Vite, Tailwind CSS, the Groq Llama 3.3 70B model, and the GitHub public Search API. Icons by Lucide.
