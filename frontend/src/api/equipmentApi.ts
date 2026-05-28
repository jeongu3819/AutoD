import type {
  EquipmentStatusResponse,
  JobStatus,
  RefreshNowResponse,
} from '../types/equipment';

const BASE = '/api/equipment/status';

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return (await res.json()) as T;
}

export function fetchCurrentStatus(): Promise<EquipmentStatusResponse> {
  return fetch(`${BASE}/current`).then((r) => handle<EquipmentStatusResponse>(r));
}

export function fetchJobStatus(): Promise<JobStatus> {
  return fetch(`${BASE}/job-status`).then((r) => handle<JobStatus>(r));
}

export function triggerRefreshNow(force = false): Promise<RefreshNowResponse> {
  const url = `${BASE}/refresh-now${force ? '?force=true' : ''}`;
  return fetch(url, { method: 'POST' }).then((r) => handle<RefreshNowResponse>(r));
}
