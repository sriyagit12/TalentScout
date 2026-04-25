"""
Pydantic schemas for the Talent Scout Agent.
These define the contracts between agents, services, and the API.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from datetime import datetime
from enum import Enum


# ============== JD PARSING ==============

class ParsedJD(BaseModel):
    """Structured representation of a job description after LLM parsing."""
    title: str
    company: Optional[str] = None
    seniority: Literal["intern", "junior", "mid", "senior", "staff", "principal", "lead"] = "mid"
    employment_type: Literal["full-time", "part-time", "contract", "internship"] = "full-time"
    location: Optional[str] = None
    remote_policy: Literal["remote", "hybrid", "onsite", "flexible"] = "flexible"
    must_have_skills: List[str] = Field(default_factory=list, description="Required technical skills")
    nice_to_have_skills: List[str] = Field(default_factory=list)
    min_years_experience: int = 0
    max_years_experience: Optional[int] = None
    domain: Optional[str] = Field(None, description="Industry/domain like fintech, healthcare, e-commerce")
    responsibilities: List[str] = Field(default_factory=list)
    salary_range: Optional[str] = None
    raw_jd: str = ""
    parsing_confidence: float = Field(0.0, ge=0.0, le=1.0)

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        """Coerce None values to sensible defaults before validation."""
        if isinstance(obj, dict):
            obj = obj.copy()
            # Replace None for enum-typed fields with defaults
            if obj.get("seniority") is None:
                obj["seniority"] = "mid"
            if obj.get("employment_type") is None:
                obj["employment_type"] = "full-time"
            if obj.get("remote_policy") is None:
                obj["remote_policy"] = "flexible"
            # Coerce None for required list/int fields
            if obj.get("must_have_skills") is None:
                obj["must_have_skills"] = []
            if obj.get("nice_to_have_skills") is None:
                obj["nice_to_have_skills"] = []
            if obj.get("responsibilities") is None:
                obj["responsibilities"] = []
            if obj.get("min_years_experience") is None:
                obj["min_years_experience"] = 0
            if obj.get("max_years_experience") is None:
                obj["max_years_experience"] = None
            if obj.get("parsing_confidence") is None:
                obj["parsing_confidence"] = 0.5
            if obj.get("title") is None or obj.get("title") == "":
                obj["title"] = "Unknown Role"
        return super().model_validate(obj, *args, **kwargs)


# ============== CANDIDATES ==============

class Candidate(BaseModel):
    """A candidate profile from any source (synthetic DB or GitHub)."""
    id: str
    name: str
    headline: str
    location: str
    years_experience: int
    skills: List[str]
    current_role: str
    current_company: Optional[str] = None
    past_companies: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    education: Optional[str] = None
    summary: str
    source: Literal["synthetic", "github"] = "synthetic"
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    open_to_opportunities: bool = True
    desired_salary: Optional[str] = None
    notice_period_days: Optional[int] = None


# ============== MATCHING ==============

class SkillMatch(BaseModel):
    skill: str
    matched: bool
    is_required: bool
    candidate_has_related: bool = False  # e.g. has React but JD asks Vue


class MatchBreakdown(BaseModel):
    """Explainable scoring breakdown — this is what the recruiter sees."""
    skills_score: float = Field(ge=0, le=100)
    experience_score: float = Field(ge=0, le=100)
    domain_score: float = Field(ge=0, le=100)
    location_score: float = Field(ge=0, le=100)
    seniority_score: float = Field(ge=0, le=100)
    skill_matches: List[SkillMatch] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    explanation: str = ""


class MatchedCandidate(BaseModel):
    candidate: Candidate
    match_score: float = Field(ge=0, le=100)
    breakdown: MatchBreakdown


# ============== CONVERSATIONAL OUTREACH ==============

class InterestArchetype(str, Enum):
    """Persona seeds for simulating realistic candidate responses."""
    EAGER = "eager"               # Actively looking, very interested
    CURIOUS = "curious"           # Open to hear more
    LUKEWARM = "lukewarm"         # Mild interest, has concerns
    PASSIVE = "passive"           # Happy where they are, but listening
    NOT_INTERESTED = "not_interested"


class OutreachChannel(str, Enum):
    EMAIL = "email"
    LINKEDIN = "linkedin"
    SMS = "sms"


class Message(BaseModel):
    sender: Literal["recruiter", "candidate"]
    channel: OutreachChannel
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    candidate_id: str
    archetype: InterestArchetype
    channel: OutreachChannel
    messages: List[Message] = Field(default_factory=list)
    completed: bool = False


# ============== INTEREST SCORING ==============

class InterestSignals(BaseModel):
    response_received: bool
    response_latency_signal: float = Field(0.0, ge=0, le=1)  # how quickly they engaged
    sentiment: float = Field(0.0, ge=-1, le=1)
    engagement_depth: float = Field(0.0, ge=0, le=1)  # length & substance of replies
    asked_questions: bool = False
    discussed_compensation: bool = False
    discussed_availability: bool = False
    raised_concerns: List[str] = Field(default_factory=list)
    positive_signals: List[str] = Field(default_factory=list)


class InterestAssessment(BaseModel):
    interest_score: float = Field(ge=0, le=100)
    signals: InterestSignals
    summary: str
    next_step_recommendation: str


# ============== FINAL SHORTLIST ==============

class ShortlistEntry(BaseModel):
    candidate: Candidate
    match_score: float
    interest_score: float
    combined_score: float
    match_breakdown: MatchBreakdown
    interest_assessment: Optional[InterestAssessment] = None
    conversation: Optional[Conversation] = None
    rank: int


class ShortlistResponse(BaseModel):
    job_id: str
    parsed_jd: ParsedJD
    total_candidates_considered: int
    shortlist: List[ShortlistEntry]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============== API REQUESTS ==============

class ScoutRequest(BaseModel):
    job_description: str = Field(min_length=50)
    max_candidates_to_engage: int = Field(default=8, ge=1, le=20)
    include_github_search: bool = True
    channels: List[OutreachChannel] = Field(default_factory=lambda: [OutreachChannel.EMAIL])


class JobStatus(BaseModel):
    job_id: str
    stage: Literal["parsing", "discovering", "matching", "engaging", "scoring", "complete", "failed"]
    progress: float = Field(ge=0, le=100)
    message: str = ""
    result: Optional[ShortlistResponse] = None
    error: Optional[str] = None
