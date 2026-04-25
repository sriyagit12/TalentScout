import React from 'react';
import { CheckCircle2, Loader2, FileSearch, Users, Target, MessageCircle, BarChart3, AlertCircle } from 'lucide-react';

const STAGES = [
  { id: 'parsing', label: 'Parsing JD', icon: FileSearch },
  { id: 'discovering', label: 'Discovering candidates', icon: Users },
  { id: 'matching', label: 'Scoring matches', icon: Target },
  { id: 'engaging', label: 'Engaging candidates', icon: MessageCircle },
  { id: 'scoring', label: 'Computing rankings', icon: BarChart3 },
];

export default function ProgressView({ status }) {
  const currentStageIdx = STAGES.findIndex((s) => s.id === status.stage);
  const isComplete = status.stage === 'complete';
  const isFailed = status.stage === 'failed';

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 md:p-8">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-slate-900 mb-2">
          {isFailed ? 'Pipeline Failed' : isComplete ? 'Done!' : 'Scouting in progress...'}
        </h2>
        <p className="text-sm text-slate-500">{status.message || 'Working on it...'}</p>
      </div>

      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex justify-between text-xs text-slate-500 mb-2">
          <span className="font-semibold">{status.progress}%</span>
          <span>Job ID: <span className="font-mono">{status.job_id}</span></span>
        </div>
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              isFailed
                ? 'bg-red-500'
                : isComplete
                ? 'bg-green-500'
                : 'bg-gradient-to-r from-brand-500 to-brand-700'
            }`}
            style={{ width: `${status.progress || 0}%` }}
          />
        </div>
      </div>

      {/* Stage list */}
      <div className="space-y-2">
        {STAGES.map((stage, idx) => {
          const isCurrent = stage.id === status.stage;
          const isDone = isComplete || idx < currentStageIdx;
          const Icon = stage.icon;

          return (
            <div
              key={stage.id}
              className={`flex items-center gap-3 p-3 rounded-lg transition ${
                isCurrent ? 'bg-brand-50' : 'bg-transparent'
              }`}
            >
              <div className={`p-1.5 rounded-md ${
                isDone ? 'bg-green-100 text-green-700'
                  : isCurrent ? 'bg-brand-100 text-brand-700'
                  : 'bg-slate-100 text-slate-400'
              }`}>
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>
              <span className={`text-sm font-medium ${
                isDone ? 'text-slate-700' : isCurrent ? 'text-brand-700' : 'text-slate-400'
              }`}>
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>

      {isFailed && status.error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-red-900">Error</p>
            <p className="text-sm text-red-700 mt-0.5">{status.error}</p>
          </div>
        </div>
      )}
    </div>
  );
}
