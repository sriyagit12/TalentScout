import React, { useState, useEffect, useRef } from 'react';
import { Sparkles, Github } from 'lucide-react';
import JDForm from './components/JDForm';
import ProgressView from './components/ProgressView';
import Shortlist from './components/Shortlist';
import { startScout, pollJob } from './api/client';

export default function App() {
  const [jobStatus, setJobStatus] = useState(null);
  const [error, setError] = useState(null);
  const stopPollingRef = useRef(null);

  useEffect(() => {
    return () => {
      if (stopPollingRef.current) stopPollingRef.current();
    };
  }, []);

  const handleSubmit = async (payload) => {
    setError(null);
    try {
      const { job_id } = await startScout(payload);
      setJobStatus({ job_id, stage: 'parsing', progress: 0, message: 'Starting...' });
      stopPollingRef.current = pollJob(job_id, (status) => setJobStatus(status), 1500);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleReset = () => {
    if (stopPollingRef.current) stopPollingRef.current();
    setJobStatus(null);
    setError(null);
  };

  const isRunning = jobStatus && !['complete', 'failed'].includes(jobStatus.stage);
  const isComplete = jobStatus?.stage === 'complete' && jobStatus.result;

  return (
    <div className="min-h-screen">
      {/* Top bar */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-brand-500 to-brand-700 rounded-lg shadow-sm">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900">Talent Scout</h1>
              <p className="text-xs text-slate-500 -mt-0.5">AI Recruiting Agent</p>
            </div>
          </div>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-slate-500 hover:text-slate-700 flex items-center gap-1.5"
          >
            <Github className="w-4 h-4" /> View source
          </a>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-4 md:px-6 py-8 md:py-12">
        {!jobStatus && !isComplete && (
          <>
            <div className="text-center mb-10">
              <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-3">
                Find &amp; engage candidates in <span className="text-brand-600">minutes</span>
              </h2>
              <p className="text-slate-600 max-w-2xl mx-auto">
                Paste a JD. Our agent parses it, finds matching candidates from a candidate
                pool + GitHub, runs simulated outreach to gauge interest, and gives you a
                ranked shortlist scored on Match × Interest.
              </p>
            </div>
            <JDForm onSubmit={handleSubmit} disabled={false} />
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {error}
              </div>
            )}
          </>
        )}

        {isRunning && <ProgressView status={jobStatus} />}

        {isComplete && (
          <Shortlist result={jobStatus.result} onReset={handleReset} />
        )}

        {jobStatus?.stage === 'failed' && (
          <div className="space-y-4">
            <ProgressView status={jobStatus} />
            <button
              onClick={handleReset}
              className="w-full py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-xl font-semibold"
            >
              Try Again
            </button>
          </div>
        )}
      </main>

      <footer className="text-center text-xs text-slate-400 py-6">
        Built with Claude Sonnet 4.6 · FastAPI · React
      </footer>
    </div>
  );
}
