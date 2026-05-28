const CARDS = [
  { key: 'total', label: '전체 관리 설비', tone: 'neutral' },
  { key: 'available', label: 'Production Available', tone: 'good' },
  { key: 'unavailable', label: 'Unavailable', tone: 'bad' },
  { key: 'run', label: 'RUN', tone: 'good' },
  { key: 'idle', label: 'IDLE', tone: 'warn-soft' },
  { key: 'down', label: 'DOWN', tone: 'bad' },
  { key: 'local', label: 'LOCAL', tone: 'warn' },
  { key: 'pm_bu', label: 'PM/BU', tone: 'work' },
  { key: 'unknown', label: 'UNKNOWN', tone: 'unknown' },
];

export default function StatusSummaryCards({ summary }) {
  return (
    <div className="summary-grid">
      {CARDS.map((c) => (
        <div key={c.key} className={`summary-card tone-${c.tone}`}>
          <div className="summary-label">{c.label}</div>
          <div className="summary-value">{summary?.[c.key] ?? 0}</div>
        </div>
      ))}
    </div>
  );
}
