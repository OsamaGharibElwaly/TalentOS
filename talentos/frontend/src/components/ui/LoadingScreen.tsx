export function Spinner({ label = '', size = 48 }: { label?: string; size?: number }) {
  return (
    <span className="loading-spinner" role="status" aria-label={label || 'Loading'}>
      <svg width={size} height={size} viewBox="0 0 56 56" fill="none" aria-hidden="true">
        <circle className="spinner-track" cx="28" cy="28" r="22" />
        <circle className="spinner-arc" cx="28" cy="28" r="22" />
        <circle className="spinner-arc spinner-arc-two" cx="28" cy="28" r="22" />
        <g className="spinner-orbit">
          <circle className="spinner-dot" cx="28" cy="6" r="2.6" />
        </g>
        <rect className="spinner-core" x="18.5" y="18.5" width="19" height="19" rx="6" />
        <path className="spinner-glyph" d="M23.6 23.5h8.8v2.9h-2.9v6.2h-3v-6.2h-2.9v-2.9Z" />
      </svg>
      {label ? <span className="muted">{label}</span> : null}
    </span>
  );
}

export function PageSkeleton() {
  return (
    <div className="page-skeleton" aria-busy="true" aria-label="Loading page">
      <div className="skeleton-hero">
        <span className="skeleton" style={{ width: 150, height: 12 }} />
        <span className="skeleton" style={{ width: '62%', height: 30 }} />
        <span className="skeleton" style={{ width: '78%', height: 12 }} />
      </div>
      <div className="stat-grid">
        {[0, 1, 2, 3].map((index) => (
          <div className="stat-card skeleton-card" key={index}>
            <span className="skeleton" style={{ width: 96, height: 12 }} />
            <span className="skeleton" style={{ width: 64, height: 34 }} />
            <span className="skeleton" style={{ width: 120, height: 10 }} />
          </div>
        ))}
      </div>
      <div className="panel skeleton-panel">
        <span className="skeleton" style={{ width: 210, height: 20 }} />
        <span className="skeleton" style={{ width: '55%', height: 11 }} />
        <div className="skeleton-lines">
          {[0, 1, 2, 3, 4].map((index) => (
            <span className="skeleton" key={index} style={{ width: `${88 - index * 8}%`, height: 10 }} />
          ))}
        </div>
      </div>
      <div className="skeleton-footnote">
        <Spinner size={18} />
        <span className="muted">Putting your workspace together…</span>
      </div>
    </div>
  );
}

export default function LoadingScreen() {
  return (
    <div className="loading-screen">
      <Spinner label="Preparing your workspace…" size={56} />
    </div>
  );
}
