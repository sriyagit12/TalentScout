// API base — empty in dev (proxy handles it), full URL in prod
const BASE = import.meta.env.VITE_API_BASE || '';

export async function startScout(payload) {
  const res = await fetch(`${BASE}/api/scout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function getJobStatus(jobId) {
  const res = await fetch(`${BASE}/api/jobs/${jobId}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export function pollJob(jobId, onUpdate, intervalMs = 2000) {
  let stopped = false;
  const tick = async () => {
    if (stopped) return;
    try {
      const status = await getJobStatus(jobId);
      onUpdate(status);
      if (status.stage === 'complete' || status.stage === 'failed') return;
    } catch (e) {
      onUpdate({ stage: 'failed', error: e.message, progress: 100 });
      return;
    }
    setTimeout(tick, intervalMs);
  };
  tick();
  return () => { stopped = true; };
}
