"""
Agent 5: Interest Scoring
Analyzes a conversation transcript to extract structured interest signals
and produce an Interest Score (0-100) plus a recommended next step.
"""
import logging
from app.models.schemas import (
    Conversation, InterestSignals, InterestAssessment
)
from app.services.llm_client import get_llm
from pydantic import BaseModel
from typing import List

logger = logging.getLogger(__name__)


class _InterestAnalysis(BaseModel):
    """Internal LLM-output schema."""
    sentiment: float
    engagement_depth: float
    asked_questions: bool
    discussed_compensation: bool
    discussed_availability: bool
    raised_concerns: List[str]
    positive_signals: List[str]
    summary: str
    next_step_recommendation: str


INTEREST_ANALYZER_SYSTEM = """You are a recruiting analyst evaluating how interested a candidate
seemed during an outreach conversation.

You will see the FULL conversation transcript between a recruiter and a candidate.
Your job: produce structured signals about the candidate's interest level.

Return JSON:
{
  "sentiment": <float -1 to 1, overall warmth/positivity of candidate's replies>,
  "engagement_depth": <float 0 to 1, how substantively the candidate engaged — short dismissive replies = 0.1, detailed thoughtful replies with questions = 0.9>,
  "asked_questions": <bool — did the candidate ask the recruiter substantive questions?>,
  "discussed_compensation": <bool — did the topic of comp/salary come up from the candidate side?>,
  "discussed_availability": <bool — did they share notice period, interview availability, or move timeline?>,
  "raised_concerns": [<list of specific concerns the candidate mentioned: e.g. "needs fully remote", "happy in current role", "wants higher comp">],
  "positive_signals": [<list of positive signals: e.g. "asked about tech stack details", "mentioned 30-day notice", "excited about the domain">],
  "summary": "1-2 sentence honest summary of the candidate's interest level",
  "next_step_recommendation": "Specific recommendation: e.g. 'Schedule intro call this week', 'Send detailed JD and follow up in 3 days', 'Park for 6 months — not currently interested', 'Move to take-home stage'"
}

Be CALIBRATED, not generous. A polite-but-uninterested response is NOT high interest.
Look at: response length, questions asked, specificity, warmth, commitment language."""


def assess_interest(conversation: Conversation) -> InterestAssessment:
    """Analyze a conversation and produce an InterestAssessment."""
    llm = get_llm()

    if not conversation.messages:
        return InterestAssessment(
            interest_score=0.0,
            signals=InterestSignals(response_received=False),
            summary="No outreach was completed.",
            next_step_recommendation="Retry outreach.",
        )

    candidate_replies = [m for m in conversation.messages if m.sender == "candidate"]
    if not candidate_replies:
        return InterestAssessment(
            interest_score=10.0,
            signals=InterestSignals(response_received=False),
            summary="Candidate did not respond to outreach.",
            next_step_recommendation="Try a different channel or send a follow-up in 5 days.",
        )

    transcript = "\n\n".join([
        f"[{m.sender.upper()} via {m.channel.value}]:\n{m.content}"
        for m in conversation.messages
    ])

    user = f"""Analyze this recruiter↔candidate conversation:

CHANNEL: {conversation.channel.value}
NUMBER OF EXCHANGES: {len(candidate_replies)}

TRANSCRIPT:
---
{transcript}
---

Return your structured analysis as JSON now."""

    try:
        analysis = llm.complete_json(
            system=INTEREST_ANALYZER_SYSTEM,
            user=user,
            schema=_InterestAnalysis,
            temperature=0.2,
            max_tokens=1200,
        )
    except Exception as e:
        logger.error(f"Interest analysis failed: {e}")
        # Fallback: neutral score
        return InterestAssessment(
            interest_score=40.0,
            signals=InterestSignals(response_received=True, sentiment=0, engagement_depth=0.4),
            summary="Analysis failed; manual review recommended.",
            next_step_recommendation="Recruiter to review transcript manually.",
        )

    # Build signals
    signals = InterestSignals(
        response_received=True,
        response_latency_signal=0.8,  # Simulated — would compute in real system
        sentiment=analysis.sentiment,
        engagement_depth=analysis.engagement_depth,
        asked_questions=analysis.asked_questions,
        discussed_compensation=analysis.discussed_compensation,
        discussed_availability=analysis.discussed_availability,
        raised_concerns=analysis.raised_concerns,
        positive_signals=analysis.positive_signals,
    )

    # Compute interest score from signals (deterministic, transparent)
    score = _compute_interest_score(signals)

    return InterestAssessment(
        interest_score=score,
        signals=signals,
        summary=analysis.summary,
        next_step_recommendation=analysis.next_step_recommendation,
    )


def _compute_interest_score(signals: InterestSignals) -> float:
    """
    Combine structured signals into a 0-100 interest score.
    Weights chosen to match recruiter intuition:
    - Sentiment matters but can be deceiving (people are polite)
    - Behavioral signals (questions, availability talk) matter MORE than tone
    - Concerns drag the score down
    """
    if not signals.response_received:
        return 5.0

    # Base from sentiment (-1..1 → 30..70)
    base = 50 + (signals.sentiment * 20)

    # Engagement depth is a strong multiplier
    depth_boost = signals.engagement_depth * 25

    # Behavioral signals
    behavior = 0
    if signals.asked_questions: behavior += 8
    if signals.discussed_availability: behavior += 12  # Strongest single signal
    if signals.discussed_compensation: behavior += 6   # Mixed — could be deal-killer or buy-signal

    # Positive signals add up; concerns subtract
    pos_boost = min(15, len(signals.positive_signals) * 4)
    concern_penalty = min(25, len(signals.raised_concerns) * 6)

    score = base + depth_boost + behavior + pos_boost - concern_penalty

    return round(max(0, min(100, score)), 1)
