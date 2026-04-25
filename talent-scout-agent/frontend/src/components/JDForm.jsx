import React, { useState } from 'react';
import { Briefcase, Sparkles, Github, Mail, Linkedin, MessageSquare, X } from 'lucide-react';

const SAMPLES = {
  'Senior Backend (Python)': `Senior Backend Engineer — Fintech

We're looking for an experienced backend engineer to help scale our payments platform serving 5M+ users.

Required:
- 6+ years building production backend systems
- Strong Python, FastAPI or Django
- PostgreSQL, Redis at scale
- AWS (EC2, RDS, Lambda)
- Docker & Kubernetes

Nice to have:
- Experience in fintech/payments domain
- Kafka or RabbitMQ
- Experience with high-availability systems

Location: Bangalore (hybrid, 3 days/week in office)
Compensation: ₹50-75 LPA depending on experience.`,

  'ML Engineer (LLM Apps)': `ML Engineer — LLM Applications

Join our small applied AI team building production RAG systems for enterprise customers.

Must have:
- 4+ years in machine learning, with at least 1 year shipping LLM-based features
- Strong Python, PyTorch
- Experience with vector databases (Pinecone, Weaviate, etc.)
- LangChain or similar orchestration frameworks
- AWS or GCP for ML deployment

Bonus:
- Hugging Face ecosystem
- Distributed training experience
- Open-source contributions

Remote-friendly (US/India hours overlap). Comp: $150k-200k or equivalent.`,

  'Casual / Slack-style': `hey! so we're a small team building a payments app and we kinda urgently need someone who knows rust really well or at least go - someone who's been around the block with distributed systems for like 5+ years. bonus if you've worked at scale before. fully remote, pays well. dm if interested`,

  'Indian-style (LPA, WFO)': `Job Title: Sr. Data Engineer
Exp: 4-7 yrs

Skills required:
SQL must - Snowflake/Redshift either fine
Python - mandatory
Airflow good to have
dbt would be plus point

CTC: 25-40 LPA neg
Loc: Bangalore - WFO 4 days
Notice: Immediate joiners preferred`,
};

export default function JDForm({ onSubmit, disabled }) {
  const [jd, setJd] = useState('');
  const [maxCandidates, setMaxCandidates] = useState(8);
  const [includeGithub, setIncludeGithub] = useState(true);
  const [channel, setChannel] = useState('email');

  const handleLoadSample = (name) => {
    // If user has typed substantial content, confirm before overwriting
    if (jd.trim().length > 20 && !window.confirm(`Replace your current JD with the "${name}" sample?`)) {
      return;
    }
    setJd(SAMPLES[name]);
  };

  const handleClear = () => {
    if (jd.trim().length > 0 && !window.confirm('Clear the textarea?')) return;
    setJd('');
  };

  const handleSubmit = () => {
    if (jd.trim().length < 50) {
      alert('Please paste a job description (at least 50 characters).');
      return;
    }
    onSubmit({
      job_description: jd,
      max_candidates_to_engage: maxCandidates,
      include_github_search: includeGithub,
      channels: [channel],
    });
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 md:p-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 bg-brand-100 rounded-xl">
          <Briefcase className="w-6 h-6 text-brand-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900">Job Description</h2>
          <p className="text-sm text-slate-500">Paste any JD — formal, casual, multilingual, or messy. Our parser handles it.</p>
        </div>
      </div>

      <div className="mb-3 flex flex-wrap gap-2 items-center">
        <span className="text-xs text-slate-500 mr-1 self-center">Or try a sample:</span>
        {Object.keys(SAMPLES).map((name) => (
          <button
            key={name}
            onClick={() => handleLoadSample(name)}
            disabled={disabled}
            className="text-xs px-3 py-1.5 rounded-full bg-slate-100 hover:bg-brand-100 hover:text-brand-700 text-slate-700 transition disabled:opacity-50"
          >
            {name}
          </button>
        ))}
        {jd.length > 0 && (
          <button
            onClick={handleClear}
            disabled={disabled}
            className="text-xs px-2.5 py-1.5 rounded-full bg-red-50 hover:bg-red-100 text-red-600 transition flex items-center gap-1 ml-auto"
          >
            <X className="w-3 h-3" /> Clear
          </button>
        )}
      </div>

      <textarea
        value={jd}
        onChange={(e) => setJd(e.target.value)}
        rows={12}
        disabled={disabled}
        className="w-full p-4 border border-slate-200 rounded-xl text-sm font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-y bg-slate-50"
        placeholder="Paste your job description here. Any format works — bullet points, prose, casual notes, abbreviations like LPA/WFO, or non-English."
      />

      <div className="mt-2 flex justify-between text-xs text-slate-400">
        <span>{jd.length} characters {jd.length < 50 && jd.length > 0 && '(need 50+ to submit)'}</span>
      </div>

      <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-2 uppercase tracking-wide">
            Candidates to engage
          </label>
          <input
            type="number"
            min={1}
            max={20}
            value={maxCandidates}
            onChange={(e) => setMaxCandidates(parseInt(e.target.value) || 8)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-2 uppercase tracking-wide">
            Outreach channel
          </label>
          <div className="flex gap-1.5">
            {[
              { id: 'email', icon: Mail, label: 'Email' },
              { id: 'linkedin', icon: Linkedin, label: 'LinkedIn' },
              { id: 'sms', icon: MessageSquare, label: 'SMS' },
            ].map(({ id, icon: Icon, label }) => (
              <button
                key={id}
                onClick={() => setChannel(id)}
                disabled={disabled}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition flex-1 justify-center ${
                  channel === id
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-2 uppercase tracking-wide">
            Sources
          </label>
          <button
            onClick={() => setIncludeGithub(!includeGithub)}
            disabled={disabled}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition w-full justify-center ${
              includeGithub
                ? 'bg-slate-900 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <Github className="w-3.5 h-3.5" />
            {includeGithub ? 'Synthetic + GitHub' : 'Synthetic only'}
          </button>
        </div>
      </div>

      <button
        onClick={handleSubmit}
        disabled={disabled || jd.trim().length < 50}
        className="mt-6 w-full bg-gradient-to-r from-brand-600 to-brand-700 hover:from-brand-700 hover:to-brand-900 text-white font-semibold py-3.5 px-6 rounded-xl shadow-sm transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <Sparkles className="w-5 h-5" />
        {disabled ? 'Scouting...' : 'Start Scouting'}
      </button>
    </div>
  );
}