/**
 * Offline Queue Service — localStorage-backed queue for interview sessions
 * and fieldwork data. Auto-flushes when online.
 *
 * Pattern: Same as analytics.ts — queue locally, batch POST when connected.
 * Used by: FieldworkTools, QuestionnaireDesign, CopilotChat
 *
 * P0 for mid-July field deployment: rural areas with unreliable 4G/5G.
 */

import { getAuthHeaders } from "../utils/authFetch";

const STORAGE_KEY = "wenjin_offline_queue";
const MAX_QUEUE = 100; // Up from 50 (analytics) — sessions are larger but rarer

export interface QueuedSession {
  /** Unique client-generated ID for dedup */
  client_id: string;
  /** Endpoint to POST to (e.g. "/fieldwork/sessions") */
  endpoint: string;
  /** Request body */
  payload: Record<string, any>;
  /** ISO timestamp when queued */
  queued_at: string;
  /** Number of retry attempts */
  retries: number;
}

// ── Connection tracking ──
let isOnline = typeof navigator !== "undefined" ? navigator.onLine : true;

function updateOnlineStatus() {
  const wasOffline = !isOnline;
  isOnline = navigator.onLine;
  if (wasOffline && isOnline) {
    flushQueue().catch(() => {});
  }
}

if (typeof window !== "undefined") {
  window.addEventListener("online", updateOnlineStatus);
  window.addEventListener("offline", () => { isOnline = false; });
}

// ── Queue management ──

function getQueue(): QueuedSession[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function persistQueue(q: QueuedSession[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(q.slice(-MAX_QUEUE)));
  } catch {
    const halved = q.slice(-Math.floor(MAX_QUEUE / 2));
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(halved)); } catch {}
  }
}

// ── Public API ──

/** Enqueue a session for later sync. Tries immediate send first; queues on failure. */
export async function enqueueSession(
  endpoint: string,
  payload: Record<string, any>,
): Promise<{ queued: boolean; client_id: string }> {
  const client_id = crypto.randomUUID();

  if (isOnline) {
    try {
      const resp = await fetch(`/api/v1${endpoint}`, {
        method: "POST",
        headers: { ...getAuthHeaders() },
        body: JSON.stringify(payload),
      });
      if (resp.ok) return { queued: false, client_id };
    } catch { /* queue below */ }
  }

  const queue = getQueue();
  queue.push({ client_id, endpoint, payload, queued_at: new Date().toISOString(), retries: 0 });
  persistQueue(queue);
  return { queued: true, client_id };
}

/** Flush all queued sessions to the server. */
export async function flushQueue(): Promise<{ flushed: number; failed: number }> {
  const queue = getQueue();
  if (queue.length === 0) return { flushed: 0, failed: 0 };

  let flushed = 0;
  let failed = 0;
  const remaining: QueuedSession[] = [];

  for (const item of queue) {
    try {
      const resp = await fetch(`/api/v1${item.endpoint}`, {
        method: "POST",
        headers: { ...getAuthHeaders() },
        body: JSON.stringify(item.payload),
      });
      if (resp.ok || (resp.status >= 400 && resp.status < 500)) {
        flushed++; // 4xx won't succeed on retry either
      } else {
        item.retries++;
        if (item.retries < 5) remaining.push(item);
        else failed++;
      }
    } catch {
      item.retries++;
      if (item.retries < 5) remaining.push(item);
      else failed++;
    }
  }

  persistQueue(remaining);
  return { flushed, failed };
}

export function getQueueSize(): number {
  return getQueue().length;
}

export function getOnlineStatus(): boolean {
  return isOnline;
}

let flushTimer: ReturnType<typeof setInterval> | null = null;

export function startAutoFlush(intervalMs: number = 60000) {
  if (flushTimer) return;
  flushTimer = setInterval(() => {
    if (getQueue().length === 0) { stopAutoFlush(); return; }
    if (isOnline) flushQueue().catch(() => {});
  }, intervalMs);
}

export function stopAutoFlush() {
  if (flushTimer) { clearInterval(flushTimer); flushTimer = null; }
}
