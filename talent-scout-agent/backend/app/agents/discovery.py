"""
Agent 2: Candidate Discovery
Hybrid source: synthetic DB (always) + GitHub API (optional, for tech roles).

Uses lightweight skill-based prefiltering so we don't waste LLM tokens
scoring obviously-bad matches.
"""
import os
import logging
from typing import List, Set
import httpx
from app.models.schemas import Candidate, ParsedJD
from app.data.synthetic_db import load_candidates

logger = logging.getLogger(__name__)

# Lazy-loaded candidate cache
_candidate_pool: List[Candidate] = []


def _get_pool() -> List[Candidate]:
    global _candidate_pool
    if not _candidate_pool:
        _candidate_pool = load_candidates()
        logger.info(f"Loaded {len(_candidate_pool)} synthetic candidates")
    return _candidate_pool


def _normalize(s: str) -> str:
    return s.lower().strip().replace(".", "").replace("-", "")


def _skill_overlap(jd_skills: Set[str], candidate_skills: List[str]) -> int:
    """Count overlapping skills (case-insensitive)."""
    cand_norm = {_normalize(s) for s in candidate_skills}
    return sum(1 for s in jd_skills if _normalize(s) in cand_norm)


def discover_synthetic(jd: ParsedJD, top_k: int = 30) -> List[Candidate]:
    """
    Prefilter synthetic pool by skill overlap. Returns top_k candidates.
    This avoids running expensive LLM matching on obviously-bad fits.
    """
    pool = _get_pool()
    must_have = {s for s in jd.must_have_skills}
    nice_have = {s for s in jd.nice_to_have_skills}
    all_jd_skills = must_have | nice_have

    scored = []
    for cand in pool:
        if not cand.open_to_opportunities:
            continue

        overlap = _skill_overlap(all_jd_skills, cand.skills)
        must_overlap = _skill_overlap(must_have, cand.skills)

        # Soft experience filter — within 50% of the range
        exp_ok = True
        if jd.min_years_experience > 0:
            exp_ok = cand.years_experience >= jd.min_years_experience * 0.5
        if jd.max_years_experience:
            exp_ok = exp_ok and cand.years_experience <= jd.max_years_experience * 1.5

        if not exp_ok:
            continue

        # Score: must-have skills weighted 3x
        score = (must_overlap * 3) + overlap
        if score > 0:
            scored.append((score, cand))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


def discover_github(jd: ParsedJD, top_k: int = 10) -> List[Candidate]:
    """
    Search GitHub for users with relevant repos.
    Uses the public Search API. Token optional but recommended (60 vs 5000 req/hr).
    Gracefully returns [] on any failure — we never want to break the demo.
    """
    if not jd.must_have_skills:
        return []

    # Pick top 1-2 most distinctive skills as language/topic queries
    primary_skill = jd.must_have_skills[0]

    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Map common skills to GitHub language names
    lang_map = {
        "python": "python", "javascript": "javascript", "typescript": "typescript",
        "react": "javascript", "node.js": "javascript", "go": "go", "rust": "rust",
        "java": "java", "kotlin": "kotlin", "swift": "swift", "ruby": "ruby",
        "c++": "cpp", "c#": "csharp", "scala": "scala",
    }
    lang = lang_map.get(primary_skill.lower(), "python")

    # Search for repos with this language and many stars; we'll grab the owners
    query = f"language:{lang} stars:>500"
    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": "stars", "per_page": top_k * 2}

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                logger.warning(f"GitHub API returned {resp.status_code}: {resp.text[:200]}")
                return []
            data = resp.json()
    except Exception as e:
        logger.warning(f"GitHub discovery failed: {e}")
        return []

    candidates = []
    seen_logins = set()
    for repo in data.get("items", [])[:top_k * 2]:
        owner = repo.get("owner", {})
        login = owner.get("login")
        if not login or login in seen_logins or owner.get("type") != "User":
            continue
        seen_logins.add(login)

        candidates.append(Candidate(
            id=f"gh_{login}",
            name=login,
            headline=f"Open-source developer ({primary_skill})",
            location="GitHub Profile",
            years_experience=4,  # Estimated — would refine with profile API call
            skills=jd.must_have_skills[:5],  # Inferred from repo language
            current_role=f"{primary_skill} Developer",
            current_company=None,
            past_companies=[],
            domains=["open-source"],
            education=None,
            summary=f"Maintains popular {lang} repo: {repo.get('name')} ({repo.get('stargazers_count', 0):,} stars). {repo.get('description', '')[:150]}",
            source="github",
            profile_url=owner.get("html_url"),
            avatar_url=owner.get("avatar_url"),
            open_to_opportunities=True,  # Optimistic assumption
            desired_salary=None,
            notice_period_days=None,
        ))

        if len(candidates) >= top_k:
            break

    logger.info(f"GitHub returned {len(candidates)} candidates")
    return candidates


def discover_candidates(
    jd: ParsedJD,
    include_github: bool = True,
    synthetic_top_k: int = 25,
    github_top_k: int = 5,
) -> List[Candidate]:
    """Combined discovery pipeline."""
    synthetic = discover_synthetic(jd, top_k=synthetic_top_k)
    github = discover_github(jd, top_k=github_top_k) if include_github else []

    # Dedupe by id (impossible across sources but good practice)
    seen = set()
    combined = []
    for c in synthetic + github:
        if c.id not in seen:
            seen.add(c.id)
            combined.append(c)

    logger.info(f"Discovered {len(combined)} candidates ({len(synthetic)} synthetic, {len(github)} github)")
    return combined
