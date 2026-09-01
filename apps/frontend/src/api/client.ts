// In dev, VITE_API_BASE_URL is unset and requests hit `/api/v1/...` via the Vite
// proxy. In production (e.g. Vercel) set it to the backend origin, such as
// `https://damga-ops-api.onrender.com`, so requests go cross-origin to that host.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const base = endpoint.startsWith('http')
    ? endpoint
    : `${API_BASE_URL}/api/v1` + (endpoint.startsWith('/') ? endpoint : `/${endpoint}`);
  const response = await fetch(base, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Client': 'DAMGA-OPS-COCKPIT',
      ...options?.headers,
    },
  });
  if (!response.ok) {
    const errorText = await response.text();
    let errorDetail = errorText;
    try {
      const json = JSON.parse(errorText);
      errorDetail = json.detail || errorText;
    } catch {}
    const err = new Error(errorDetail);
    (err as any).status = response.status;
    throw err;
  }
  return response.json();
}
