import type { PrcGroupSummary, RiskLevel } from '../types/equipment';

function RiskBadge({ level }: { level: RiskLevel }) {
  return <span className={`risk-badge risk-${level.toLowerCase()}`}>{level}</span>;
}

interface Props {
  rows?: PrcGroupSummary[] | null;
}

export default function ToolGroupSummaryTable({ rows }: Props) {
  if (!rows?.length) {
    return <div className="empty-block">설비군별 데이터가 없습니다.</div>;
  }
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>PRC_GROUP</th>
          <th>전체</th>
          <th>가용</th>
          <th>비가용</th>
          <th>위험도</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.prc_group}>
            <td>{r.prc_group}</td>
            <td>{r.total}</td>
            <td className="cell-good">{r.available}</td>
            <td className="cell-bad">{r.unavailable}</td>
            <td>
              <RiskBadge level={r.risk_level} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
