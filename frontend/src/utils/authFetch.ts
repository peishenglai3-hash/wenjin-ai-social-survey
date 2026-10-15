/**
 * Authenticated fetch helper — wraps native fetch with JWT Bearer token.
 *
 * Use this for raw fetch calls that need authentication. For Axios-based
 * API calls, use api/client.ts which already has interceptors.
 */

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  try {
    const saved = localStorage.getItem("wenjin_auth");
    if (saved) {
      const { access_token } = JSON.parse(saved);
      if (access_token) headers["Authorization"] = `Bearer ${access_token}`;
    }
  } catch { /* ignore */ }
  return headers;
}

/**
 * Fetch wrapper that automatically includes JWT auth headers.
 * Falls back gracefully if no token is stored (for public endpoints).
 */
export async function authFetch(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  const authHeaders = getAuthHeaders();
  return fetch(url, {
    ...options,
    headers: {
      ...authHeaders,
      ...(options.headers as Record<string, string> || {}),
    },
  });
}

export { getAuthHeaders };
