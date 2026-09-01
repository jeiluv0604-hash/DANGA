export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const base = endpoint.startsWith('http')
    ? endpoint
    : `/api/v1` + (endpoint.startsWith('/') ? endpoint : `/${endpoint}`);
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
