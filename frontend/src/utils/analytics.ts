/**
 * Lightweight analytics/telemetry for Wenjin (问津).
 *
 * Events are POSTed to /api/v1/analytics/events.
 * Offline events are queued in localStorage and flushed on next successful send.
 * Keep this file under 80 lines.
 */

const STORAGE_KEY = "wenjin_analytics_queue";
const MAX_QUEUE = 50;

function getSessionId(): string {
  let sid = sessionStorage.getItem("wenjin_sid");
  if (!sid) {
    sid = crypto.randomUUID();
    sessionStorage.setItem("wenjin_sid", sid);
  }
  return sid;
}

function getOrCreateQueue(): any[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function persistQueue(q: any[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(q.slice(-MAX_QUEUE)));
  } catch { /* storage full — drop oldest */ }
}

async function flushQueue(): Promise<void> {
  const queue = getOrCreateQueue();
  if (queue.length === 0) return;
  try {
    const resp = await fetch("/api/v1/analytics/events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ events: queue }),
    });
    if (resp.ok) localStorage.removeItem(STORAGE_KEY);
  } catch { /* offline — keep queued */ }
}

async function sendEvent(
  eventName: string,
  properties?: Record<string, any>
): Promise<void> {
  const event = {
    event_name: eventName,
    properties: properties || {},
    session_id: getSessionId(),
    timestamp: new Date().toISOString(),
  };
  // Try flush first (LIFO batch)
  await flushQueue();
  try {
    const resp = await fetch("/api/v1/analytics/events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ events: [event] }),
    });
    if (!resp.ok) throw new Error("send failed");
  } catch {
    const q = getOrCreateQueue();
    q.push(event);
    persistQueue(q);
  }
}

export function trackEvent(eventName: string, properties?: Record<string, any>) {
  sendEvent(eventName, properties).catch(() => { /* fire-and-forget */ });
}

export function trackPageView(pageName: string) {
  trackEvent("page_view", { page: pageName, url: window.location.pathname });
}

export function trackSearch(
  query: string,
  filters: Record<string, any>,
  resultCount: number
) {
  trackEvent("search", { query, filters, result_count: resultCount });
}
