import { useCallback, useEffect, useRef, useState } from 'react';
import StatusSummaryCards from '../components/StatusSummaryCards';
import LineSummaryTable from '../components/LineSummaryTable';
import ToolGroupSummaryTable from '../components/ToolGroupSummaryTable';
import EquipmentStatusTable from '../components/EquipmentStatusTable';
import RefreshBar from '../components/RefreshBar';
import SchedulerStatusPanel from '../components/SchedulerStatusPanel';
import {
  fetchCurrentStatus,
  fetchJobStatus,
  triggerRefreshNow,
} from '../api/equipmentApi';
import type { EquipmentStatusResponse, JobStatus } from '../types/equipment';

const SCREEN_REFRESH_MS = 30_000;

export default function EquipmentStatusPage() {
  const [current, setCurrent] = useState<EquipmentStatusResponse | null>(null);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [cur, j] = await Promise.all([fetchCurrentStatus(), fetchJobStatus()]);
      setCurrent(cur);
      setJob(j);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  const onForceCollect = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await triggerRefreshNow(false);
      const [cur, j] = await Promise.all([fetchCurrentStatus(), fetchJobStatus()]);
      setCurrent(cur);
      setJob(j);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
    timerRef.current = setInterval(reload, SCREEN_REFRESH_MS);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [reload]);

  return (
    <div className="page">
      <header className="page-header">
        <h1>준실시간 설비 상태 모니터링</h1>
        <p className="page-subtitle">
          Lake 기준 최신 상태를 표시합니다. Datalake 적재 주기: 약 10분
          {current?.source_file && (
            <span className="source-file"> · {current.source_file}</span>
          )}
        </p>
      </header>

      {error && <div className="error-banner">에러: {error}</div>}

      <RefreshBar
        lakeStatusDate={current?.lake_status_date}
        lastCollectedAt={current?.last_collected_at}
        lastApiResponseTime={current?.last_api_response_time}
        onManualRefresh={reload}
        onForceCollect={onForceCollect}
        loading={loading}
      />

      <SchedulerStatusPanel job={job} />

      <section>
        <h2>요약</h2>
        <StatusSummaryCards summary={current?.summary} />
      </section>

      <section>
        <h2>라인별 요약</h2>
        <LineSummaryTable rows={current?.line_summary} />
      </section>

      <section>
        <h2>PRC_GROUP별 요약</h2>
        <ToolGroupSummaryTable rows={current?.prc_group_summary} />
      </section>

      <section>
        <h2>설비 상태</h2>
        <EquipmentStatusTable items={current?.items ?? []} />
      </section>
    </div>
  );
}
