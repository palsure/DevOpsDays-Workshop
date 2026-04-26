import { useCallback, useEffect, useState } from 'react';

const API = '/api/v1/pipeline-runs';

type PlatformDto = {
  platform: string;
  passed: number;
  failed: number;
  skipped: number;
  total: number;
};

type RunDto = {
  runId: string;
  status: string;
  githubRunId: string | null;
  gateThreshold: number;
  overallPassRate: number | null;
  overallPassRatePercent: number | null;
  createdAt: string;
  finalizedAt: string | null;
  platforms: PlatformDto[];
};

async function readJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || res.statusText);
  }
  return res.json() as Promise<T>;
}

export function PipelinePage({ onBack }: { onBack: () => void }) {
  const [run, setRun] = useState<RunDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loadLatest = useCallback(async () => {
    setError(null);
    try {
      const res = await fetch(`${API}/latest`);
      if (res.status === 404) {
        setRun(null);
        return;
      }
      setRun(await readJson<RunDto>(res));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void loadLatest();
  }, [loadLatest]);

  const postPlatform = async (
    runId: string,
    platform: string,
    passed: number,
    failed: number,
    skipped: number,
    total: number,
  ) => {
    const res = await fetch(`${API}/${runId}/platforms`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform, passed, failed, skipped, total }),
    });
    await readJson(res);
  };

  const finalize = async (runId: string) => {
    const res = await fetch(`${API}/${runId}/finalize`, { method: 'POST' });
    return readJson<RunDto>(res);
  };

  const runScenario = async (mode: 'pass' | 'fail') => {
    setBusy(true);
    setError(null);
    try {
      const created = await readJson<{ runId: string }>(
        await fetch(API, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ githubRunId: `demo-${mode}-${Date.now()}` }),
        }),
      );
      const rid = created.runId;

      const platforms = ['api', 'web', 'android', 'ios', 'automation'] as const;
      for (const p of platforms) {
        if (mode === 'pass') {
          await postPlatform(rid, p, 9, 1, 0, 10);
        } else {
          await postPlatform(rid, p, 6, 4, 0, 10);
        }
      }
      const done = await finalize(rid);
      setRun(done);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const pct = run?.overallPassRatePercent != null ? run.overallPassRatePercent.toFixed(1) : '—';
  const gatePct = (run?.gateThreshold ?? 0.8) * 100;

  return (
    <div className="pipeline-page">
      <header className="pipeline-header">
        <button type="button" className="pipeline-back" onClick={onBack}>
          ← Back
        </button>
        <h1>Build acceptance &amp; release gate</h1>
        <p className="pipeline-lede">
          Mirrors CI: each platform reports test counts; the API aggregates <strong>passed / total</strong> and
          marks the run <strong>RELEASED</strong> if the rate is at least {(0.8 * 100).toFixed(0)}% (configurable on
          the server), otherwise <strong>BLOCKED</strong>.
        </p>
      </header>

      <section className="pipeline-actions">
        <button type="button" onClick={() => void loadLatest()} disabled={busy}>
          Refresh latest run
        </button>
        <button type="button" onClick={() => void runScenario('pass')} disabled={busy}>
          Demo: simulate CI (≥80% — released)
        </button>
        <button type="button" onClick={() => void runScenario('fail')} disabled={busy}>
          Demo: simulate CI (&lt;80% — blocked)
        </button>
      </section>

      {error && <div className="pipeline-error" role="alert">{error}</div>}

      {run && (
        <section className="pipeline-result">
          <div className={`pipeline-verdict pipeline-verdict--${run.status.toLowerCase()}`}>
            <span className="pipeline-verdict-label">{run.status}</span>
            <span className="pipeline-verdict-rate">
              Pass rate: {pct}% (gate: {gatePct.toFixed(0)}%)
            </span>
          </div>
          <p className="pipeline-meta">
            Run <code>{run.runId}</code>
            {run.githubRunId && (
              <>
                {' '}
                · Git ref <code>{run.githubRunId}</code>
              </>
            )}
          </p>
          <table className="pipeline-table">
            <thead>
              <tr>
                <th>Platform</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Skipped</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {run.platforms.map(row => (
                <tr key={row.platform}>
                  <td>{row.platform}</td>
                  <td>{row.passed}</td>
                  <td>{row.failed}</td>
                  <td>{row.skipped}</td>
                  <td>{row.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {!run && !error && (
        <p className="pipeline-empty">No pipeline runs yet — use a demo button or hit the API from CI.</p>
      )}
    </div>
  );
}
