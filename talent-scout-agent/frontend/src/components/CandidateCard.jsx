import React, { useState } from 'react';
import {
  Github, MapPin, Briefcase, GraduationCap, Building2, Mail, Linkedin, MessageSquare,
  ChevronDown, ChevronUp, TrendingUp, Heart, Award, AlertTriangle, CheckCircle2,
  XCircle, MinusCircle, MessageCircle, Calendar, DollarSign, ExternalLink,
} from 'lucide-react';

function ScoreBar({ label, value, color = 'brand' }) {
  const colors = {
    brand: 'bg-brand-500',
    green: 'bg-green-500',
    amber: 'bg-amber-500',
    red: 'bg-red-500',
    slate: 'bg-slate-400',
  };
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-600 font-medium">{label}</span>
        <span className="font-bold text-slate-900">{Math.round(value)}</span>
      </div>
      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${colors[color]} transition-all duration-700`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

function scoreColor(score) {
  if (score >= 75) return 'green';
  if (score >= 55) return 'amber';
  return 'red';
}

function archetypeBadge(archetype) {
  const map = {
    eager: { label: '🔥 Eager', cls: 'bg-green-100 text-green-700' },
    curious: { label: '👀 Curious', cls: 'bg-blue-100 text-blue-700' },
    lukewarm: { label: '🤷 Lukewarm', cls: 'bg-amber-100 text-amber-700' },
    passive: { label: '😐 Passive', cls: 'bg-slate-100 text-slate-700' },
    not_interested: { label: '🚫 Declined', cls: 'bg-red-100 text-red-700' },
  };
  return map[archetype] || { label: archetype, cls: 'bg-slate-100 text-slate-700' };
}

function channelIcon(ch) {
  if (ch === 'email') return Mail;
  if (ch === 'linkedin') return Linkedin;
  return MessageSquare;
}

export default function CandidateCard({ entry }) {
  const [expanded, setExpanded] = useState(false);
  const [showConversation, setShowConversation] = useState(false);
  const { candidate, match_score, interest_score, combined_score, match_breakdown, interest_assessment, conversation, rank } = entry;

  const ChannelIcon = conversation ? channelIcon(conversation.channel) : Mail;
  const archetype = conversation ? archetypeBadge(conversation.archetype) : null;
  const isGithub = candidate.source === 'github';

  return (
    <div className={`bg-white rounded-2xl shadow-sm border-2 transition-all overflow-hidden ${
      rank === 1 ? 'border-brand-300 shadow-brand-100' : 'border-slate-200'
    }`}>
      {/* Header — always visible */}
      <div className="p-5">
        <div className="flex items-start gap-4">
          {/* Rank badge */}
          <div className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg ${
            rank === 1 ? 'bg-gradient-to-br from-amber-400 to-orange-500 text-white shadow-md'
              : rank === 2 ? 'bg-gradient-to-br from-slate-300 to-slate-400 text-white'
              : rank === 3 ? 'bg-gradient-to-br from-orange-300 to-amber-600 text-white'
              : 'bg-slate-100 text-slate-600'
          }`}>
            #{rank}
          </div>

          {/* Avatar */}
          <img
            src={candidate.avatar_url}
            alt={candidate.name}
            className="w-12 h-12 rounded-full border-2 border-slate-100"
            onError={(e) => { e.target.style.display = 'none'; }}
          />

          {/* Identity */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-lg font-bold text-slate-900">{candidate.name}</h3>
              {isGithub && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-900 text-white text-xs rounded-full">
                  <Github className="w-3 h-3" /> GitHub
                </span>
              )}
              {archetype && (
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${archetype.cls}`}>
                  {archetype.label}
                </span>
              )}
            </div>
            <p className="text-sm text-slate-600 truncate">{candidate.headline}</p>
            <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-500 flex-wrap">
              <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{candidate.location}</span>
              <span className="flex items-center gap-1"><Briefcase className="w-3 h-3" />{candidate.years_experience}y</span>
              {candidate.education && (
                <span className="flex items-center gap-1"><GraduationCap className="w-3 h-3" />{candidate.education}</span>
              )}
            </div>
          </div>

          {/* Combined score */}
          <div className="flex-shrink-0 text-right">
            <div className={`text-3xl font-extrabold ${
              combined_score >= 75 ? 'text-green-600' : combined_score >= 55 ? 'text-amber-600' : 'text-red-600'
            }`}>
              {Math.round(combined_score)}
            </div>
            <div className="text-xs text-slate-500 font-medium uppercase tracking-wide">Combined</div>
          </div>
        </div>

        {/* Match + Interest summary scores */}
        <div className="grid grid-cols-2 gap-3 mt-5">
          <div className="p-3 bg-slate-50 rounded-lg">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-slate-600 flex items-center gap-1">
                <Award className="w-3.5 h-3.5" /> Match Score
              </span>
              <span className="text-lg font-bold text-slate-900">{Math.round(match_score)}</span>
            </div>
            <div className="h-1.5 bg-white rounded-full overflow-hidden">
              <div className="h-full bg-brand-500" style={{ width: `${match_score}%` }} />
            </div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-slate-600 flex items-center gap-1">
                <Heart className="w-3.5 h-3.5" /> Interest Score
              </span>
              <span className="text-lg font-bold text-slate-900">{Math.round(interest_score)}</span>
            </div>
            <div className="h-1.5 bg-white rounded-full overflow-hidden">
              <div className="h-full bg-pink-500" style={{ width: `${interest_score}%` }} />
            </div>
          </div>
        </div>

        {/* Quick explanation */}
        {match_breakdown.explanation && (
          <p className="mt-4 text-sm text-slate-700 italic leading-relaxed">
            "{match_breakdown.explanation}"
          </p>
        )}

        {/* Interest summary */}
        {interest_assessment && (
          <div className="mt-3 p-3 bg-pink-50 border border-pink-100 rounded-lg">
            <p className="text-sm text-slate-700 leading-relaxed">
              <span className="font-semibold text-pink-700">Outreach result:</span> {interest_assessment.summary}
            </p>
            <p className="mt-1.5 text-xs text-pink-600 font-medium">
              ⮕ {interest_assessment.next_step_recommendation}
            </p>
          </div>
        )}

        {/* Expand button */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-4 w-full text-sm text-brand-600 hover:text-brand-700 font-medium flex items-center justify-center gap-1 py-2 hover:bg-brand-50 rounded-lg transition"
        >
          {expanded ? 'Hide details' : 'Show details'}
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-slate-100 bg-slate-50/50 p-5 space-y-5">
          {/* Score breakdown */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide mb-3">Match Score Breakdown</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <ScoreBar label="Skills" value={match_breakdown.skills_score} color={scoreColor(match_breakdown.skills_score)} />
              <ScoreBar label="Experience" value={match_breakdown.experience_score} color={scoreColor(match_breakdown.experience_score)} />
              <ScoreBar label="Seniority Match" value={match_breakdown.seniority_score} color={scoreColor(match_breakdown.seniority_score)} />
              <ScoreBar label="Domain" value={match_breakdown.domain_score} color={scoreColor(match_breakdown.domain_score)} />
              <ScoreBar label="Location" value={match_breakdown.location_score} color={scoreColor(match_breakdown.location_score)} />
            </div>
          </div>

          {/* Strengths & Gaps */}
          <div className="grid md:grid-cols-2 gap-4">
            {match_breakdown.strengths?.length > 0 && (
              <div className="p-3 bg-green-50 border border-green-100 rounded-lg">
                <h5 className="text-xs font-bold text-green-700 uppercase mb-2 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Strengths
                </h5>
                <ul className="space-y-1">
                  {match_breakdown.strengths.map((s, i) => (
                    <li key={i} className="text-sm text-slate-700 flex gap-1.5">
                      <span className="text-green-600">•</span>{s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {match_breakdown.gaps?.length > 0 && (
              <div className="p-3 bg-amber-50 border border-amber-100 rounded-lg">
                <h5 className="text-xs font-bold text-amber-700 uppercase mb-2 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" /> Gaps
                </h5>
                <ul className="space-y-1">
                  {match_breakdown.gaps.map((g, i) => (
                    <li key={i} className="text-sm text-slate-700 flex gap-1.5">
                      <span className="text-amber-600">•</span>{g}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Per-skill match grid */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide mb-2">Skill-by-Skill Match</h4>
            <div className="flex flex-wrap gap-1.5">
              {match_breakdown.skill_matches.map((sm, i) => (
                <span key={i} className={`text-xs px-2.5 py-1 rounded-full font-medium flex items-center gap-1 ${
                  sm.matched
                    ? 'bg-green-100 text-green-800'
                    : sm.candidate_has_related
                    ? 'bg-amber-100 text-amber-800'
                    : sm.is_required
                    ? 'bg-red-100 text-red-800'
                    : 'bg-slate-100 text-slate-600'
                }`}>
                  {sm.matched ? <CheckCircle2 className="w-3 h-3" />
                    : sm.candidate_has_related ? <MinusCircle className="w-3 h-3" />
                    : <XCircle className="w-3 h-3" />}
                  {sm.skill}{sm.is_required ? '*' : ''}
                </span>
              ))}
            </div>
            <p className="text-[11px] text-slate-400 mt-2">
              * = required. Green = exact match. Amber = related skill. Red = missing required.
            </p>
          </div>

          {/* Profile details */}
          <div className="grid md:grid-cols-2 gap-3 text-sm">
            <div className="flex items-center gap-2 text-slate-600">
              <Building2 className="w-4 h-4 text-slate-400" />
              <span>Past: {candidate.past_companies?.join(', ') || 'N/A'}</span>
            </div>
            {candidate.desired_salary && (
              <div className="flex items-center gap-2 text-slate-600">
                <DollarSign className="w-4 h-4 text-slate-400" />
                <span>Desired: {candidate.desired_salary}</span>
              </div>
            )}
            {candidate.notice_period_days != null && (
              <div className="flex items-center gap-2 text-slate-600">
                <Calendar className="w-4 h-4 text-slate-400" />
                <span>Notice: {candidate.notice_period_days} days</span>
              </div>
            )}
            {candidate.profile_url && (
              <a
                href={candidate.profile_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-brand-600 hover:text-brand-700 font-medium"
              >
                <ExternalLink className="w-4 h-4" /> View profile
              </a>
            )}
          </div>

          {/* Interest signals */}
          {interest_assessment?.signals && (
            <div>
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide mb-2">Interest Signals</h4>
              <div className="flex flex-wrap gap-1.5">
                {interest_assessment.signals.asked_questions && (
                  <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full">Asked questions</span>
                )}
                {interest_assessment.signals.discussed_availability && (
                  <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">Discussed availability</span>
                )}
                {interest_assessment.signals.discussed_compensation && (
                  <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full">Discussed comp</span>
                )}
                <span className="text-xs px-2 py-1 bg-slate-100 text-slate-700 rounded-full">
                  Sentiment: {(interest_assessment.signals.sentiment * 100).toFixed(0)}
                </span>
                <span className="text-xs px-2 py-1 bg-slate-100 text-slate-700 rounded-full">
                  Engagement: {(interest_assessment.signals.engagement_depth * 100).toFixed(0)}%
                </span>
              </div>
              {interest_assessment.signals.positive_signals?.length > 0 && (
                <div className="mt-3 text-xs">
                  <span className="font-semibold text-green-700">Positive: </span>
                  <span className="text-slate-600">{interest_assessment.signals.positive_signals.join(' · ')}</span>
                </div>
              )}
              {interest_assessment.signals.raised_concerns?.length > 0 && (
                <div className="mt-1 text-xs">
                  <span className="font-semibold text-amber-700">Concerns: </span>
                  <span className="text-slate-600">{interest_assessment.signals.raised_concerns.join(' · ')}</span>
                </div>
              )}
            </div>
          )}

          {/* Conversation transcript */}
          {conversation?.messages?.length > 0 && (
            <div>
              <button
                onClick={() => setShowConversation(!showConversation)}
                className="flex items-center gap-2 text-sm font-semibold text-brand-700 hover:text-brand-900"
              >
                <MessageCircle className="w-4 h-4" />
                {showConversation ? 'Hide' : 'View'} conversation transcript
                <ChannelIcon className="w-3.5 h-3.5" />
                ({conversation.messages.length} messages)
              </button>
              {showConversation && (
                <div className="mt-3 space-y-3">
                  {conversation.messages.map((msg, i) => (
                    <div
                      key={i}
                      className={`flex ${msg.sender === 'recruiter' ? 'justify-start' : 'justify-end'}`}
                    >
                      <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
                        msg.sender === 'recruiter'
                          ? 'bg-white border border-slate-200 text-slate-800'
                          : 'bg-brand-600 text-white'
                      }`}>
                        <div className={`text-[10px] font-bold uppercase tracking-wider mb-1 ${
                          msg.sender === 'recruiter' ? 'text-slate-400' : 'text-brand-100'
                        }`}>
                          {msg.sender === 'recruiter' ? 'Recruiter' : candidate.name.split(' ')[0]}
                        </div>
                        <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
