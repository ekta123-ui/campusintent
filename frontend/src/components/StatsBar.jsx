export default function StatsBar({ stats }) {
  if (!stats) return <p className="muted">Backend not reachable. Start it with: python -m uvicorn api.main:app --reload</p>;
  const items = [
    ["Knowledge entries", stats.kb_entries],
    ["Questions saved", stats.questions_saved],
    ["Waiting for staff", stats.unanswered],
  ];
  return (
    <div className="stats-wrap">
      <div className="stats">
        {items.map(([k, v]) => (
          <div key={k} className="stat"><strong key={String(v)}>{v}</strong><span>{k}</span></div>
        ))}
      </div>
      <p className="stats-meta muted">{stats.backend} · {stats.embedder}{stats.llm ? " · Claude" : ""}</p>
    </div>
  );
}
