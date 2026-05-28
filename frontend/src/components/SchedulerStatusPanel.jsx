function fmt(ts) {
  if (!ts) return '-';
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleString();
}

export default function SchedulerStatusPanel({ job }) {
  if (!job) return null;
  return (
    <div className="scheduler-panel">
      <div className="scheduler-panel__title">Scheduler 상태</div>
      <div className="scheduler-grid">
        <div><span className="label">Scheduler 상태</span><span className="value">{job.scheduler_enabled ? 'RUNNING' : 'STOPPED'}</span></div>
        <div><span className="label">수집 주기</span><span className="value">{job.poll_interval_seconds}s</span></div>
        <div><span className="label">마지막 체크 시각</span><span className="value">{fmt(job.last_check_time)}</span></div>
        <div><span className="label">마지막 Lake status_date</span><span className="value">{fmt(job.last_lake_status_date)}</span></div>
        <div><span className="label">마지막 full query 시각</span><span className="value">{fmt(job.last_success_collect_time)}</span></div>
        <div><span className="label">마지막 skip 사유</span><span className="value">{job.last_full_query_skipped_reason || '-'}</span></div>
        <div><span className="label">마지막 에러</span><span className={`value ${job.last_error_message ? 'value-error' : ''}`}>{job.last_error_message || '-'}</span></div>
        <div><span className="label">다음 실행 예정 시각</span><span className="value">{fmt(job.next_run_time)}</span></div>
      </div>
    </div>
  );
}
