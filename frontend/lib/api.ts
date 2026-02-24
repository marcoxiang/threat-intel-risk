const PUBLIC_API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const INTERNAL_API_BASE = process.env.API_INTERNAL_URL || PUBLIC_API_BASE;
const DEFAULT_USER = process.env.NEXT_PUBLIC_DEMO_USER || 'analyst';
const DEFAULT_ROLE = process.env.NEXT_PUBLIC_DEMO_ROLE || 'Reviewer';

function resolveApiBase() {
  return typeof window === 'undefined' ? INTERNAL_API_BASE : PUBLIC_API_BASE;
}

export async function apiGet(path: string) {
  const base = resolveApiBase();
  let res: Response;
  try {
    res = await fetch(`${base}${path}`, {
      cache: 'no-store',
      headers: {
        'X-User': DEFAULT_USER,
        'X-Role': DEFAULT_ROLE,
      },
    });
  } catch (err) {
    const detail = err instanceof Error ? err.message : 'network error';
    throw new Error(`Unable to reach API at ${base}. ${detail}`);
  }
  if (!res.ok) {
    throw new Error(`API request failed (${res.status}) for ${path}`);
  }
  return res.json();
}

export async function apiPost(path: string, body: unknown) {
  const base = resolveApiBase();
  let res: Response;
  try {
    res = await fetch(`${base}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User': DEFAULT_USER,
        'X-Role': DEFAULT_ROLE,
      },
      body: JSON.stringify(body),
    });
  } catch (err) {
    const detail = err instanceof Error ? err.message : 'network error';
    throw new Error(`Unable to reach API at ${base}. ${detail}`);
  }
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API request failed (${res.status}) for ${path}: ${detail}`);
  }
  return res.json();
}

export function apiBase() {
  return resolveApiBase();
}

export function authHeaders() {
  return {
    'X-User': DEFAULT_USER,
    'X-Role': DEFAULT_ROLE,
  };
}
