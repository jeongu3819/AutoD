function fmt(ts: string | null | undefined): string {
  if (!ts) return '-';
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleString();
}

interface Props {
  lakeStatusDate: string | null | undefined;
  platformCollectedTime: string | null | undefined;
  lastApiResponseTime: string | null | undefined;
  onManualRefresh: () => void;
  onForceCollect: () => void;
  loading: boolean;
}

export default function RefreshBar({
  lakeStatusDate,
  platformCollectedTime,
  lastApiResponseTime,
  onManualRefresh,
  onForceCollect,
  loading,
}: Props) {
  return (
    <div className="refresh-bar">
      <div className="refresh-bar__times">
        <div>
          <span className="label">Lake 데이터 기준 시각:</span>
          <span className="value">{fmt(lakeStatusDate)}</span>
        </div>
        <div>
          <span className="label">플랫폼 수집 시각:</span>
          <span className="value">{fmt(platformCollectedTime)}</span>
        </div>
        <div>
          <span className="label">화면 갱신 시각:</span>
          <span className="value">{fmt(lastApiResponseTime)}</span>
        </div>
      </div>
      <div className="refresh-bar__actions">
        <button onClick={onManualRefresh} disabled={loading}>
          화면 새로고침
        </button>
        <button onClick={onForceCollect} disabled={loading} className="secondary">
          데이터 즉시 수집
        </button>
      </div>
    </div>
  );
}
