import { useCallback, useEffect, useRef, useState } from 'react';
import StatusSummaryCards from '../components/StatusSummaryCards.jsx';
import LineSummaryTable from '../components/LineSummaryTable.jsx';
import ToolGroupSummaryTable from '../components/ToolGroupSummaryTable.jsx';
import EquipmentStatusTable from '../components/EquipmentStatusTable.jsx';
import RefreshBar from '../components/RefreshBar.jsx';
import SchedulerStatusPanel from '../components/SchedulerStatusPanel.jsx';
import {
  fetchCurrentStatus,
  fetchJobStatus,
  triggerRefreshNow,
} from '../api/equipmentApi.js';

const SCREEN_REFRESH_MS = 30_000;

export default function EquipmentStatusPage() {
  const [current, setCurrent] = useState(null);
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [cur, j] = await Promise.all([fetchCurrentStatus(), fetchJobStatus()]);
      setCurrent(cur);
      setJob(j);
    } catch (e) {
      setError(String(e?.message || e));
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
      setError(String(e?.message || e));
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
        </p>
      </header>

      {error && <div className="error-banner">에러: {error}</div>}

      <RefreshBar
        lakeStatusDate={current?.lake_status_date}
        platformCollectedTime={current?.platform_collected_time}
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
        <h2>설비군별 요약</h2>
        <ToolGroupSummaryTable rows={current?.tool_group_summary} />
      </section>

      <section>
        <h2>설비 상태</h2>
        <EquipmentStatusTable items={current?.items ?? []} />
      </section>
    </div>
  );
}
