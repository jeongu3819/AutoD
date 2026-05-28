const BASE = '/api/equipment/status';

async function handle(res) {
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json();
}

export function fetchCurrentStatus() {
  return fetch(`${BASE}/current`).then(handle);
}

export function fetchJobStatus() {
  return fetch(`${BASE}/job-status`).then(handle);
}

export function triggerRefreshNow(force = false) {
  const url = `${BASE}/refresh-now${force ? '?force=true' : ''}`;
  return fetch(url, { method: 'POST' }).then(handle);
}
