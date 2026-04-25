"""
Orchestrator: runs the full 5-stage pipeline.

Stage 1: Parse JD
Stage 2: Discover candidates (synthetic + GitHub)
Stage 3: Match & score candidates (top N kept)
Stage 4: Engage top candidates conversationally (parallel)
Stage 5: Score interest from conversations
Final: Combined ranked shortlist

Job state is kept in-memory (fine for prototype). For production,
swap _JOBS for Redis or a DB.
"""
import logging
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict
from app.models.schemas import (
    ScoutRequest, JobStatus, ParsedJD, ShortlistResponse, ShortlistEntry,
    OutreachChannel, MatchedCandidate,
)
from app.agents.jd_parser import parse_jd
from app.agents.discovery import discover_candidates
from app.agents.matcher import match_candidates
from app.agents.outreach import run_outreach_simulation
from app.agents.interest_scorer import assess_interest

logger = logging.getLogger(__name__)


# In-memory job store
_JOBS: Dict[str, JobStatus] = {}


def get_job(job_id: str) -> JobStatus | None:
    return _JOBS.get(job_id)


def list_jobs() -> list[JobStatus]:
    return list(_JOBS.values())


def _update(job_id: str, **kwargs):
    if job_id in _JOBS:
        for k, v in kwargs.items():
            setattr(_JOBS[job_id], k, v)


def _engage_one(matched: MatchedCandidate, jd: ParsedJD, channel: OutreachChannel):
    """Run outreach + interest scoring for a single candidate. Returns (conv, assessment)."""
    try:
        conv = run_outreach_simulation(
            candidate=matched.candidate,
            jd=jd,
            channel=channel,
            max_turns=3,
        )
        assessment = assess_interest(conv)
        return conv, assessment
    except Exception as e:
        logger.error(f"Engagement failed for {matched.candidate.id}: {e}")
        return None, None


def run_pipeline(job_id: str, request: ScoutRequest):
    """
    Run the full pipeline. This is blocking — designed to run in a background
    thread via FastAPI's BackgroundTasks.
    """
    try:
        # ===== STAGE 1: Parse JD =====
        _update(job_id, stage="parsing", progress=5, message="Parsing job description...")
        parsed = parse_jd(request.job_description)
        logger.info(f"[{job_id}] Parsed JD: {parsed.title} | {len(parsed.must_have_skills)} must-haves")
        _update(job_id, progress=15, message=f"Parsed: {parsed.title}")

        # ===== STAGE 2: Discover =====
        _update(job_id, stage="discovering", progress=20, message="Discovering candidates...")
        candidates = discover_candidates(
            parsed,
            include_github=request.include_github_search,
            synthetic_top_k=25,
            github_top_k=5,
        )
        logger.info(f"[{job_id}] Discovered {len(candidates)} candidates")
        _update(job_id, progress=35, message=f"Found {len(candidates)} candidates")

        if not candidates:
            _update(job_id, stage="failed", progress=100,
                    error="No candidates found matching the JD requirements.")
            return

        # ===== STAGE 3: Match =====
        _update(job_id, stage="matching", progress=40, message="Scoring candidates...")
        matched = match_candidates(candidates, parsed)
        # Keep the top N for engagement (scoring all of them with conversations is wasteful)
        top_for_engagement = matched[:request.max_candidates_to_engage]
        logger.info(f"[{job_id}] Matched. Top score: {matched[0].match_score if matched else 0}")
        _update(job_id, progress=60, message=f"Top {len(top_for_engagement)} selected for outreach")

        # ===== STAGE 4: Engage (parallel) =====
        _update(job_id, stage="engaging", progress=65,
                message=f"Reaching out to {len(top_for_engagement)} candidates...")

        # Use first channel selected, default to email
        channel = request.channels[0] if request.channels else OutreachChannel.EMAIL

        # Parallelize outreach — each candidate is independent
        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(_engage_one, m, parsed, channel)
                for m in top_for_engagement
            ]
            for i, (m, future) in enumerate(zip(top_for_engagement, futures)):
                conv, assessment = future.result()
                results.append((m, conv, assessment))
                # Update progress as each completes
                pct = 65 + int(25 * (i + 1) / len(top_for_engagement))
                _update(job_id, progress=pct,
                        message=f"Engaged {i+1}/{len(top_for_engagement)} candidates")

        # ===== STAGE 5: Combined ranking =====
        _update(job_id, stage="scoring", progress=92, message="Computing final rankings...")

        entries = []
        for m, conv, assessment in results:
            interest_score = assessment.interest_score if assessment else 0.0
            # Combined score: 60% match, 40% interest
            # (match weighted higher because it's harder to "fake" via politeness)
            combined = 0.60 * m.match_score + 0.40 * interest_score
            entries.append(ShortlistEntry(
                candidate=m.candidate,
                match_score=m.match_score,
                interest_score=interest_score,
                combined_score=round(combined, 1),
                match_breakdown=m.breakdown,
                interest_assessment=assessment,
                conversation=conv,
                rank=0,  # set below
            ))

        entries.sort(key=lambda e: e.combined_score, reverse=True)
        for i, e in enumerate(entries):
            e.rank = i + 1

        result = ShortlistResponse(
            job_id=job_id,
            parsed_jd=parsed,
            total_candidates_considered=len(candidates),
            shortlist=entries,
            generated_at=datetime.utcnow(),
        )

        _update(job_id, stage="complete", progress=100,
                message=f"Done. {len(entries)} candidates ranked.",
                result=result)
        logger.info(f"[{job_id}] Pipeline complete")

    except Exception as e:
        logger.exception(f"[{job_id}] Pipeline failed")
        _update(job_id, stage="failed", progress=100, error=str(e))


def create_job(request: ScoutRequest) -> str:
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    _JOBS[job_id] = JobStatus(
        job_id=job_id,
        stage="parsing",
        progress=0,
        message="Job queued...",
    )
    return job_id
