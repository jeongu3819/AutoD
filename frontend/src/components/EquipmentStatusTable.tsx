import { useMemo, useState } from 'react';
import type { EquipmentStatusItem } from '../types/equipment';

function statusBadgeClass(normalized: string): string {
  switch (normalized) {
    case 'RUN':
    case 'BU_DONE':
      return 'badge badge-good';
    case 'IDLE':
      return 'badge badge-warn-soft';
    case 'DOWN':
    case 'BU_FAIL':
      return 'badge badge-bad';
    case 'LOCAL':
      return 'badge badge-warn';
    case 'PM_PROGRESS':
    case 'PM_DONE':
    case 'BU_WAIT':
    case 'BU_PROGRESS':
      return 'badge badge-work';
    case 'HOLD':
      return 'badge badge-hold';
    default:
      return 'badge badge-unknown';
  }
}

function collectBadgeClass(status: string | null): string {
  if (status === 'SUCCESS') return 'badge badge-good';
  if (status === 'NO_DATA') return 'badge badge-warn';
  return 'badge badge-unknown';
}

function formatTs(value: string | null | undefined): string {
  if (!value) return '-';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

type AvailFilter = 'ALL' | 'AVAIL' | 'UNAVAIL';

interface Props {
  items: EquipmentStatusItem[];
}

export default function EquipmentStatusTable({ items }: Props) {
  const [lineFilter, setLineFilter] = useState<string>('ALL');
  const [groupFilter, setGroupFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [availFilter, setAvailFilter] = useState<AvailFilter>('ALL');
  const [search, setSearch] = useState<string>('');

  const lines = useMemo(
    () => Array.from(new Set(items.map((i) => i.lineid))).sort(),
    [items],
  );
  const groups = useMemo(
    () => Array.from(new Set(items.map((i) => i.PRC_GROUP ?? ''))).filter(Boolean).sort(),
    [items],
  );
  const statuses = useMemo(
    () => Array.from(new Set(items.map((i) => i.normalized_status))).sort(),
    [items],
  );

  const filtered = useMemo(() => {
    return items.filter((i) => {
      if (lineFilter !== 'ALL' && i.lineid !== lineFilter) return false;
      if (groupFilter !== 'ALL' && i.PRC_GROUP !== groupFilter) return false;
      if (statusFilter !== 'ALL' && i.normalized_status !== statusFilter) return false;
      if (availFilter === 'AVAIL' && !i.production_available) return false;
      if (availFilter === 'UNAVAIL' && i.production_available) return false;
      if (search) {
        const q = search.toLowerCase();
        const hay = `${i.lineid} ${i.eqpid} ${i.PRC_GROUP ?? ''} ${i.area ?? ''}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [items, lineFilter, groupFilter, statusFilter, availFilter, search]);

  return (
    <div className="equipment-status-table">
      <div className="filter-row">
        <label>
          라인
          <select value={lineFilter} onChange={(e) => setLineFilter(e.target.value)}>
            <option value="ALL">전체</option>
            {lines.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </label>
        <label>
          PRC_GROUP
          <select value={groupFilter} onChange={(e) => setGroupFilter(e.target.value)}>
            <option value="ALL">전체</option>
            {groups.map((g) => <option key={g} value={g}>{g}</option>)}
          </select>
        </label>
        <label>
          상태
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="ALL">전체</option>
            {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <label>
          Production
          <select
            value={availFilter}
            onChange={(e) => setAvailFilter(e.target.value as AvailFilter)}
          >
            <option value="ALL">전체</option>
            <option value="AVAIL">가용</option>
            <option value="UNAVAIL">비가용</option>
          </select>
        </label>
        <label className="search-label">
          검색
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="라인 / 설비 / PRC_GROUP"
          />
        </label>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>라인</th>
            <th>설비</th>
            <th>PRC_GROUP</th>
            <th>현재 상태</th>
            <th>이전 상태</th>
            <th>상태 전환</th>
            <th>정규화 상태</th>
            <th>Production</th>
            <th>상태 기준 시각</th>
            <th>최초 DOWN 시각</th>
            <th>백업 시각</th>
            <th>수집 상태</th>
            <th>수집 시각</th>
          </tr>
        </thead>
        <tbody>
          {filtered.length === 0 ? (
            <tr>
              <td colSpan={13} className="empty-cell">조건에 맞는 설비가 없습니다.</td>
            </tr>
          ) : (
            filtered.map((i) => (
              <tr key={`${i.lineid}-${i.eqpid}`}>
                <td>{i.lineid}</td>
                <td>{i.eqpid}</td>
                <td>{i.PRC_GROUP ?? '-'}</td>
                <td>{i.status ?? '-'}</td>
                <td>{i.pre_status ?? '-'}</td>
                <td className="cell-transition">
                  {i.pre_status || '-'} → {i.status || '-'}
                </td>
                <td>
                  <span className={statusBadgeClass(i.normalized_status)}>
                    {i.normalized_status}
                  </span>
                </td>
                <td>
                  {i.production_available ? (
                    <span className="badge badge-good">가용</span>
                  ) : (
                    <span className="badge badge-bad">비가용</span>
                  )}
                </td>
                <td>{formatTs(i.status_date)}</td>
                <td>{formatTs(i.first_down_date)}</td>
                <td>{formatTs(i.backup_date)}</td>
                <td>
                  <span className={collectBadgeClass(i.collect_status)}>
                    {i.collect_status ?? '-'}
                  </span>
                </td>
                <td>{formatTs(i.collected_at)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
