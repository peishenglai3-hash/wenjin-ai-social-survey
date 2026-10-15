import axios from "axios";
import config from "../config";

const api = axios.create({
  baseURL: `${config.apiBaseUrl}/api/v1`,
  timeout: 120000,
});

// ── 401 Refresh Queue ─────────────────────────────────────
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: any) => void;
}> = [];

function getToken(): string | null {
  try {
    const saved = localStorage.getItem("wenjin_auth");
    if (saved) return JSON.parse(saved).access_token || null;
  } catch { /* ignore */ }
  return null;
}

function processQueue(error: any, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
}

// Request interceptor — inject Bearer token (skip for guest)
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token && token !== "guest") {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — handle 401 with auto-refresh
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config;

    // Only attempt refresh for 401s that aren't auth endpoints themselves
    if (
      err.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/auth/login") &&
      !originalRequest.url?.includes("/auth/register") &&
      !originalRequest.url?.includes("/auth/refresh")
    ) {
      // Try to get the refresh token from storage
      let storedRefreshToken: string | null = null;
      try {
        const saved = localStorage.getItem("wenjin_auth");
        if (saved) storedRefreshToken = JSON.parse(saved).refresh_token || null;
      } catch { /* ignore */ }

      if (!storedRefreshToken) {
        // No refresh token — just reject
        return Promise.reject(err);
      }

      if (isRefreshing) {
        // Queue this request until refresh completes
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch(() => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const resp = await axios.post(
          `${config.apiBaseUrl}/api/v1/auth/refresh`,
          { refresh_token: storedRefreshToken },
        );
        const { access_token: newAccess, refresh_token: newRefresh } = resp.data;
        // Update storage
        localStorage.setItem(
          "wenjin_auth",
          JSON.stringify({ access_token: newAccess, refresh_token: newRefresh }),
        );
        processQueue(null, newAccess);
        originalRequest.headers.Authorization = `Bearer ${newAccess}`;
        return api(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        // Clear auth — force re-login
        localStorage.removeItem("wenjin_auth");
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    console.error("API error:", err.message);
    return Promise.reject(err);
  },
);

export default api;
