import React, { useState } from 'react';
import { Users, Award, Heart, TrendingUp, Filter, Download, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import CandidateCard from './CandidateCard';

export default function Shortlist({ result, onReset }) {
  const [filter, setFilter] = useState('all');
  const [showJD, setShowJD] = useState(false);

  const filtered = result.shortlist.filter((e) => {
    if (filter === 'all') return true;
    if (filter === 'top') return e.combined_score >= 70;
    if (filter === 'engaged') return e.interest_score >= 50;
    return true;
  });

  const stats = {
    total: result.total_candidates_considered,
    shortlisted: result.shortlist.length,
    avgMatch: Math.round(result.shortlist.reduce((sum, e) => sum + e.match_score, 0) / result.shortlist.length || 0),
    avgInterest: Math.round(result.shortlist.reduce((sum, e) => sum + e.interest_score, 0) / result.shortlist.length || 0),
    hot: result.shortlist.filter((e) => e.combined_score >= 70).length,
  };

  const handleExport = () => {
    const csv = [
      ['Rank', 'Name', 'Headline', 'Location', 'Years', 'Match Score', 'Interest Score', 'Combined', 'Next Step'].join(','),
      ...result.shortlist.map((e) => [
        e.rank,
        `"${e.candidate.name}"`,
        `"${e.candidate.headline}"`,
        `"${e.candidate.location}"`,
        e.candidate.years_experience,
        e.match_score,
        e.interest_score,
        e.combined_score,
        `"${e.interest_assessment?.next_step_recommendation || ''}"`,
      ].join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `shortlist_${result.job_id}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">{result.parsed_jd.title}</h2>
            <p className="text-sm text-slate-500 mt-1">
              {result.parsed_jd.seniority} · {result.parsed_jd.location || 'Any'} · {result.parsed_jd.remote_policy}
              {result.parsed_jd.domain && ` · ${result.parsed_jd.domain}`}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium flex items-center gap-2 transition"
            >
              <Download className="w-4 h-4" /> Export CSV
            </button>
            <button
              onClick={onReset}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-medium transition"
            >
              New Search
            </button>
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-6">
          <Stat icon={Users} label="Considered" value={stats.total} color="slate" />
          <Stat icon={Award} label="Shortlisted" value={stats.shortlisted} color="brand" />
          <Stat icon={TrendingUp} label="Avg Match" value={stats.avgMatch} color="green" />
          <Stat icon={Heart} label="Avg Interest" value={stats.avgInterest} color="pink" />
          <Stat icon={Award} label="Top fits (70+)" value={stats.hot} color="amber" />
        </div>

        {/* JD breakdown toggle */}
        <button
          onClick={() => setShowJD(!showJD)}
          className="mt-5 text-sm text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1"
        >
          <FileText className="w-4 h-4" />
          {showJD ? 'Hide' : 'View'} parsed JD requirements
          {showJD ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showJD && (
          <div className="mt-3 p-4 bg-slate-50 rounded-lg space-y-2 text-sm">
            <div>
              <span className="font-semibold text-slate-700">Must have:</span>{' '}
              <span className="text-slate-600">{result.parsed_jd.must_have_skills.join(' · ')}</span>
            </div>
            {result.parsed_jd.nice_to_have_skills.length > 0 && (
              <div>
                <span className="font-semibold text-slate-700">Nice to have:</span>{' '}
                <span className="text-slate-600">{result.parsed_jd.nice_to_have_skills.join(' · ')}</span>
              </div>
            )}
            <div>
              <span className="font-semibold text-slate-700">Experience:</span>{' '}
              <span className="text-slate-600">
                {result.parsed_jd.min_years_experience}+ years
                {result.parsed_jd.max_years_experience && ` (max ${result.parsed_jd.max_years_experience})`}
              </span>
            </div>
            {result.parsed_jd.responsibilities.length > 0 && (
              <div>
                <span className="font-semibold text-slate-700">Responsibilities:</span>
                <ul className="list-disc list-inside text-slate-600 mt-1 ml-2">
                  {result.parsed_jd.responsibilities.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}
            <div className="text-xs text-slate-500 pt-2 border-t border-slate-200">
              Parsing confidence: {Math.round((result.parsed_jd.parsing_confidence || 0) * 100)}%
            </div>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <Filter className="w-4 h-4 text-slate-400" />
        {[
          { id: 'all', label: 'All candidates', count: result.shortlist.length },
          { id: 'top', label: 'Top fits (70+)', count: stats.hot },
          { id: 'engaged', label: 'Engaged (50+ interest)', count: result.shortlist.filter((e) => e.interest_score >= 50).length },
        ].map((f) => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            className={`text-sm px-3 py-1.5 rounded-full font-medium transition ${
              filter === f.id
                ? 'bg-brand-600 text-white'
                : 'bg-white border border-slate-200 text-slate-700 hover:border-brand-300'
            }`}
          >
            {f.label} <span className="opacity-70">({f.count})</span>
          </button>
        ))}
      </div>

      {/* Candidate list */}
      <div className="space-y-4">
        {filtered.map((entry) => (
          <CandidateCard key={entry.candidate.id} entry={entry} />
        ))}
        {filtered.length === 0 && (
          <div className="text-center py-12 text-slate-500 text-sm">
            No candidates match this filter.
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({ icon: Icon, label, value, color }) {
  const colors = {
    slate: 'text-slate-700 bg-slate-100',
    brand: 'text-brand-700 bg-brand-100',
    green: 'text-green-700 bg-green-100',
    pink: 'text-pink-700 bg-pink-100',
    amber: 'text-amber-700 bg-amber-100',
  };
  return (
    <div className="p-3 bg-slate-50 rounded-lg">
      <div className={`inline-flex p-1.5 rounded-md ${colors[color]} mb-1.5`}>
        <Icon className="w-3.5 h-3.5" />
      </div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      <div className="text-xs text-slate-500 font-medium">{label}</div>
    </div>
  );
}
