export default function LineSummaryTable({ rows }) {
  if (!rows?.length) {
    return <div className="empty-block">라인별 데이터가 없습니다.</div>;
  }
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Line</th>
          <th>전체</th>
          <th>가용</th>
          <th>비가용</th>
          <th>RUN</th>
          <th>DOWN</th>
          <th>LOCAL</th>
          <th>PM/BU</th>
          <th>UNKNOWN</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.lineid}>
            <td>{r.lineid}</td>
            <td>{r.total}</td>
            <td className="cell-good">{r.available}</td>
            <td className="cell-bad">{r.unavailable}</td>
            <td>{r.run}</td>
            <td>{r.down}</td>
            <td>{r.local}</td>
            <td>{r.pm_bu}</td>
            <td>{r.unknown}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
