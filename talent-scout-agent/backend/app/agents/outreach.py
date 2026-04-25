"""
Agent 4: Conversational Outreach Simulator

Two LLMs in a loop:
- Recruiter LLM: writes outreach + follow-ups, channel-aware tone
- Candidate LLM: responds based on their profile + a random "interest archetype"

The archetype is hidden from the recruiter LLM — that's the whole point of
the simulation. The recruiter must INFER interest from the conversation,
which is exactly what the interest scorer does next.
"""
import random
import logging
from app.models.schemas import (
    Candidate, ParsedJD, Conversation, Message,
    InterestArchetype, OutreachChannel,
)
from app.services.llm_client import get_llm

logger = logging.getLogger(__name__)


# ============== ARCHETYPE PROFILES ==============
# These seed the candidate LLM. They're hidden from the recruiter side.

ARCHETYPE_PROMPTS = {
    InterestArchetype.EAGER: """You are actively job hunting and EXCITED about new opportunities.
- Reply quickly and warmly
- Ask substantive questions about the role
- Volunteer your availability and notice period
- Show enthusiasm about the company/tech stack
- May proactively ask about compensation""",

    InterestArchetype.CURIOUS: """You are not actively looking but OPEN to hear about good opportunities.
- Reply professionally, with measured warmth
- Ask 1-2 thoughtful questions about the role
- Don't over-commit — you want to learn more before deciding
- Mention your current role positively but acknowledge interest""",

    InterestArchetype.LUKEWARM: """You are happy in your current role but POLITELY engaging.
- Reply briefly and somewhat formally
- Mention you're not really looking right now
- Ask one clarifying question, but don't push for more
- Be honest about what would have to be true for you to consider moving (e.g., remote, comp bump)""",

    InterestArchetype.PASSIVE: """You are flattered but NOT particularly looking.
- Reply briefly and politely
- Acknowledge the message but say you're focused on current role
- Don't ask many questions
- Leave the door open for the future without committing to a conversation""",

    InterestArchetype.NOT_INTERESTED: """You are NOT interested in moving.
- Reply curtly but politely
- Decline the opportunity clearly
- May or may not give a reason (e.g., "happy where I am", "just moved", "not the right tech")
- Do not ask questions or engage further""",
}


def _pick_archetype() -> InterestArchetype:
    """Weighted distribution that's realistic — most people are passive/lukewarm."""
    return random.choices(
        list(ARCHETYPE_PROMPTS.keys()),
        weights=[15, 30, 25, 20, 10],  # eager, curious, lukewarm, passive, not_interested
        k=1
    )[0]


# ============== RECRUITER LLM ==============

def _channel_style(channel: OutreachChannel) -> str:
    if channel == OutreachChannel.EMAIL:
        return ("Email format: include a subject line on the first message only "
                "(format: 'Subject: ...\\n\\n<body>'). Professional but warm tone. "
                "2-3 short paragraphs max.")
    if channel == OutreachChannel.LINKEDIN:
        return ("LinkedIn InMail: no subject line. Conversational, slightly informal. "
                "Lead with personalization. 100-150 words max.")
    return ("SMS: very short, 1-3 sentences. No subject. Casual but professional. "
            "Maximum 280 characters.")


def _generate_recruiter_message(
    candidate: Candidate,
    jd: ParsedJD,
    channel: OutreachChannel,
    history: list[Message],
) -> str:
    """Generate a recruiter outreach message — initial or follow-up."""
    llm = get_llm()
    is_initial = len(history) == 0

    system = f"""You are a thoughtful technical recruiter reaching out to a passive candidate.
{_channel_style(channel)}

Goals:
- {'Open the conversation' if is_initial else 'Continue the conversation naturally based on their reply'}
- Reference 1-2 SPECIFIC things from the candidate's profile (don't be generic)
- Briefly pitch the role's most attractive aspects
- {'Ask a low-friction question to invite reply' if is_initial else 'Address their questions/concerns honestly, then ask one clarifying question or propose a next step'}

Hard rules:
- No emoji-spam, no buzzwords ("synergy", "rockstar", "ninja")
- Don't claim things about the company you weren't told
- Be honest if you don't have an answer
- {'Personalize beyond just their name and current company' if is_initial else 'Match their energy level; do not be more enthusiastic than they are'}"""

    history_text = "\n\n".join([
        f"[{m.sender.upper()}]: {m.content}" for m in history
    ]) if history else "(no prior messages)"

    user = f"""ROLE BEING RECRUITED FOR:
{jd.title} — {jd.seniority} level
Skills sought: {', '.join(jd.must_have_skills[:6])}
Domain: {jd.domain or 'general'}
Location: {jd.location or 'flexible'} ({jd.remote_policy})
Salary: {jd.salary_range or 'competitive, depends on candidate'}
Top responsibilities: {'; '.join(jd.responsibilities[:3])}

CANDIDATE YOU'RE MESSAGING:
{candidate.name} — {candidate.headline}
Current: {candidate.current_role} at {candidate.current_company}
Skills: {', '.join(candidate.skills[:8])}
Background: {candidate.summary}

CONVERSATION SO FAR ({channel.value}):
{history_text}

Write your {'opening message' if is_initial else 'next reply'} now. Output ONLY the message text, no commentary."""

    return llm.complete(system=system, user=user, temperature=0.7, max_tokens=600).strip()


# ============== CANDIDATE LLM ==============

def _generate_candidate_reply(
    candidate: Candidate,
    archetype: InterestArchetype,
    jd: ParsedJD,
    channel: OutreachChannel,
    history: list[Message],
) -> str:
    """Generate a candidate response based on their hidden archetype."""
    llm = get_llm()

    system = f"""You are roleplaying as a real candidate responding to recruiter outreach.

YOUR PROFILE (this is YOU):
Name: {candidate.name}
Current role: {candidate.current_role} at {candidate.current_company}
Years experience: {candidate.years_experience}
Skills: {', '.join(candidate.skills)}
Location: {candidate.location}
Background: {candidate.summary}
Notice period: {candidate.notice_period_days or 'unspecified'} days
Desired comp (only mention if asked or if archetype says to): {candidate.desired_salary or 'not yet shared'}

YOUR INTEREST LEVEL & STYLE:
{ARCHETYPE_PROMPTS[archetype]}

CHANNEL: {channel.value} — keep your reply length appropriate to the channel
({'short, 1-3 sentences' if channel == OutreachChannel.SMS else 'normal email/message length, 1-3 short paragraphs'})

RULES:
- Stay in character. Don't break the fourth wall.
- Reply naturally — real candidates don't write essays
- Be authentic, including imperfect grammar/casualness if your archetype calls for it
- Don't list bullet points like a corporate doc — write like a human typing on their phone
- Output ONLY your reply text. No subject line, no signature beyond a casual "—{candidate.name.split()[0]}" if it fits."""

    history_text = "\n\n".join([
        f"[{m.sender.upper()}]: {m.content}" for m in history
    ])

    user = f"""The recruiter just sent you this message via {channel.value}:

CONVERSATION SO FAR:
{history_text}

Write your reply now, in character."""

    return llm.complete(system=system, user=user, temperature=0.85, max_tokens=500).strip()


# ============== ORCHESTRATION ==============

def run_outreach_simulation(
    candidate: Candidate,
    jd: ParsedJD,
    channel: OutreachChannel = OutreachChannel.EMAIL,
    max_turns: int = 3,
    archetype: InterestArchetype = None,
) -> Conversation:
    """
    Run a full conversation: recruiter opens → candidate replies → recruiter follows up → ...

    max_turns counts EXCHANGES (one recruiter msg + one candidate reply each).
    For NOT_INTERESTED archetype, we end early after one exchange.
    """
    if archetype is None:
        archetype = _pick_archetype()

    conversation = Conversation(
        candidate_id=candidate.id,
        archetype=archetype,
        channel=channel,
        messages=[],
    )

    for turn in range(max_turns):
        # Recruiter sends
        try:
            recruiter_msg = _generate_recruiter_message(
                candidate, jd, channel, conversation.messages
            )
            conversation.messages.append(Message(
                sender="recruiter", channel=channel, content=recruiter_msg
            ))
        except Exception as e:
            logger.error(f"Recruiter LLM failed for {candidate.id}: {e}")
            break

        # Candidate replies
        try:
            candidate_reply = _generate_candidate_reply(
                candidate, archetype, jd, channel, conversation.messages
            )
            conversation.messages.append(Message(
                sender="candidate", channel=channel, content=candidate_reply
            ))
        except Exception as e:
            logger.error(f"Candidate LLM failed for {candidate.id}: {e}")
            break

        # End early if not interested
        if archetype == InterestArchetype.NOT_INTERESTED and turn == 0:
            break

        # End early for passive after 2 turns
        if archetype == InterestArchetype.PASSIVE and turn >= 1:
            break

    conversation.completed = True
    return conversation
