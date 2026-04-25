"""
Agent 3: Matching & Scoring with Explainability
Computes Match Score (0-100) for each candidate against the parsed JD.

Hybrid approach:
- Deterministic scoring for skills/experience/location (fast, transparent)
- LLM-generated explanation for the recruiter (the "why")
This keeps scores reproducible while still being explainable.
"""
import logging
from typing import List
from app.models.schemas import (
    Candidate, ParsedJD, MatchedCandidate, MatchBreakdown, SkillMatch
)
from app.services.llm_client import get_llm

logger = logging.getLogger(__name__)


# Related-skill heuristics — extend as needed
RELATED_SKILLS = {
    "react": ["next.js", "redux", "javascript", "typescript"],
    "vue.js": ["nuxt.js", "javascript"],
    "node.js": ["express", "typescript", "javascript"],
    "python": ["django", "fastapi", "flask"],
    "django": ["python", "fastapi"],
    "fastapi": ["python", "django"],
    "kubernetes": ["docker", "helm"],
    "docker": ["kubernetes"],
    "aws": ["gcp", "azure"],
    "postgresql": ["mysql", "sql"],
    "mongodb": ["nosql"],
    "tensorflow": ["pytorch", "scikit-learn"],
    "pytorch": ["tensorflow", "transformers"],
    "swift": ["swiftui", "ios"],
    "kotlin": ["jetpack compose", "android"],
}


def _normalize(s: str) -> str:
    return s.lower().strip().replace(".", "").replace("-", "")


def _compute_skill_matches(
    candidate: Candidate, jd: ParsedJD
) -> tuple[List[SkillMatch], float]:
    """Returns (per-skill match list, skills_score 0-100)."""
    cand_skills_norm = {_normalize(s) for s in candidate.skills}
    matches: List[SkillMatch] = []

    must_total = len(jd.must_have_skills)
    must_matched = 0
    must_related = 0
    nice_matched = 0

    for skill in jd.must_have_skills:
        norm = _normalize(skill)
        if norm in cand_skills_norm:
            must_matched += 1
            matches.append(SkillMatch(skill=skill, matched=True, is_required=True))
        else:
            related = [_normalize(r) for r in RELATED_SKILLS.get(norm, [])]
            has_related = any(r in cand_skills_norm for r in related)
            if has_related:
                must_related += 1
            matches.append(SkillMatch(
                skill=skill, matched=False, is_required=True,
                candidate_has_related=has_related
            ))

    for skill in jd.nice_to_have_skills:
        norm = _normalize(skill)
        matched = norm in cand_skills_norm
        if matched:
            nice_matched += 1
        matches.append(SkillMatch(skill=skill, matched=matched, is_required=False))

    # Skills score: must-haves dominate. Related skills give partial credit.
    if must_total == 0:
        skills_score = 60.0  # Neutral if no must-haves specified
    else:
        must_pct = (must_matched + 0.4 * must_related) / must_total
        skills_score = 70 * must_pct

        # Bonus for nice-to-haves
        if jd.nice_to_have_skills:
            nice_pct = nice_matched / len(jd.nice_to_have_skills)
            skills_score += 30 * nice_pct
        else:
            skills_score += 15  # Half credit if no nice-to-haves listed

    return matches, min(100, skills_score)


def _compute_experience_score(candidate: Candidate, jd: ParsedJD) -> float:
    """Rewards being in the desired band, gentle penalty outside."""
    if jd.min_years_experience == 0 and jd.max_years_experience is None:
        return 75.0

    min_y = jd.min_years_experience
    max_y = jd.max_years_experience or (min_y + 5)
    exp = candidate.years_experience

    if min_y <= exp <= max_y:
        return 100.0
    if exp < min_y:
        gap = min_y - exp
        return max(20.0, 100 - gap * 25)  # -25 per year under
    # Overqualified
    over = exp - max_y
    return max(40.0, 100 - over * 10)  # Lighter penalty for being over


def _compute_seniority_score(candidate: Candidate, jd: ParsedJD) -> float:
    seniority_titles = {
        "intern": ["intern"],
        "junior": ["junior", "associate"],
        "mid": [""],
        "senior": ["senior"],
        "staff": ["staff"],
        "principal": ["principal"],
        "lead": ["lead", "tech lead"],
    }
    expected_terms = seniority_titles.get(jd.seniority, [])
    role_lower = candidate.current_role.lower()
    if any(term and term in role_lower for term in expected_terms):
        return 100.0
    if jd.seniority == "mid" and not any(
        t in role_lower for t in ["senior", "staff", "principal", "lead", "junior", "intern"]
    ):
        return 90.0
    return 60.0


def _compute_domain_score(candidate: Candidate, jd: ParsedJD) -> float:
    if not jd.domain:
        return 75.0
    if jd.domain.lower() in [d.lower() for d in candidate.domains]:
        return 100.0
    return 50.0


def _compute_location_score(candidate: Candidate, jd: ParsedJD) -> float:
    if jd.remote_policy == "remote":
        return 100.0
    if not jd.location:
        return 80.0
    cand_loc = candidate.location.lower()
    jd_loc = jd.location.lower()
    # Crude city/country matching — production would geocode
    if any(part.strip() in cand_loc for part in jd_loc.split(",")):
        return 100.0
    if "remote" in cand_loc:
        return 70.0 if jd.remote_policy in ["hybrid", "flexible"] else 40.0
    return 35.0


def _generate_explanation(
    candidate: Candidate, jd: ParsedJD, breakdown: MatchBreakdown
) -> tuple[str, List[str], List[str]]:
    """Use LLM to write a human-readable explanation with strengths and gaps."""
    llm = get_llm()

    matched_skills = [m.skill for m in breakdown.skill_matches if m.matched]
    missing_required = [m.skill for m in breakdown.skill_matches
                        if not m.matched and m.is_required and not m.candidate_has_related]
    related_only = [m.skill for m in breakdown.skill_matches
                    if not m.matched and m.is_required and m.candidate_has_related]

    system = """You are a recruiting analyst. Given a candidate, a JD, and a scoring breakdown,
write a SHORT, SHARP explanation a recruiter can read in 10 seconds.

Return JSON:
{
  "explanation": "2-3 sentences total. Plain English. Lead with the strongest signal.",
  "strengths": ["max 3 short bullets, each <12 words"],
  "gaps": ["max 3 short bullets, each <12 words; honest about what's missing"]
}

Be specific. Reference actual skills/experience. No fluff."""

    user = f"""JOB:
Title: {jd.title}
Seniority: {jd.seniority} ({jd.min_years_experience}+ years)
Must-have skills: {', '.join(jd.must_have_skills)}
Nice-to-have: {', '.join(jd.nice_to_have_skills)}
Domain: {jd.domain or 'any'}
Location: {jd.location or 'any'} ({jd.remote_policy})

CANDIDATE:
{candidate.name} — {candidate.headline}
{candidate.years_experience} years experience, in {candidate.location}
Current role: {candidate.current_role} at {candidate.current_company or 'N/A'}
Skills: {', '.join(candidate.skills)}
Domains: {', '.join(candidate.domains)}
Summary: {candidate.summary}

SCORING:
Skills: {breakdown.skills_score:.0f}/100 (matched {len(matched_skills)}/{len(jd.must_have_skills)} required)
Experience: {breakdown.experience_score:.0f}/100
Seniority: {breakdown.seniority_score:.0f}/100
Domain: {breakdown.domain_score:.0f}/100
Location: {breakdown.location_score:.0f}/100

Matched skills: {matched_skills}
Missing required: {missing_required}
Has related (not exact): {related_only}
"""

    class _Explanation:
        explanation: str
        strengths: list
        gaps: list

    from pydantic import BaseModel
    class ExplanationModel(BaseModel):
        explanation: str
        strengths: List[str]
        gaps: List[str]

    try:
        result = llm.complete_json(
            system=system, user=user, schema=ExplanationModel,
            temperature=0.4, max_tokens=500,
        )
        return result.explanation, result.strengths, result.gaps
    except Exception as e:
        logger.warning(f"Explanation generation failed for {candidate.id}: {e}")
        # Fallback: deterministic explanation
        return (
            f"Matches {len(matched_skills)}/{len(jd.must_have_skills)} required skills with "
            f"{candidate.years_experience}y experience.",
            matched_skills[:3],
            missing_required[:3],
        )


def score_candidate(candidate: Candidate, jd: ParsedJD) -> MatchedCandidate:
    """Compute full match breakdown for one candidate."""
    skill_matches, skills_score = _compute_skill_matches(candidate, jd)
    exp_score = _compute_experience_score(candidate, jd)
    sen_score = _compute_seniority_score(candidate, jd)
    dom_score = _compute_domain_score(candidate, jd)
    loc_score = _compute_location_score(candidate, jd)

    # Weighted total: skills dominate (50%)
    total = (
        0.50 * skills_score +
        0.20 * exp_score +
        0.10 * sen_score +
        0.10 * dom_score +
        0.10 * loc_score
    )

    breakdown = MatchBreakdown(
        skills_score=skills_score,
        experience_score=exp_score,
        seniority_score=sen_score,
        domain_score=dom_score,
        location_score=loc_score,
        skill_matches=skill_matches,
    )

    explanation, strengths, gaps = _generate_explanation(candidate, jd, breakdown)
    breakdown.explanation = explanation
    breakdown.strengths = strengths
    breakdown.gaps = gaps

    return MatchedCandidate(
        candidate=candidate,
        match_score=round(total, 1),
        breakdown=breakdown,
    )


def match_candidates(candidates: List[Candidate], jd: ParsedJD) -> List[MatchedCandidate]:
    """Score and rank all candidates."""
    matched = [score_candidate(c, jd) for c in candidates]
    matched.sort(key=lambda m: m.match_score, reverse=True)
    return matched
