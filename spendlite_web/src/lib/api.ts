import type { HistoryMessage, SessionSummary } from "./events";

async function json<T>(res: Response, what: string): Promise<T> {
  if (!res.ok) throw new Error(`${what} failed (${res.status})`);
  return (await res.json()) as T;
}

export async function listSessions(): Promise<SessionSummary[]> {
  return json(await fetch("/api/sessions"), "listSessions");
}

export async function createSession(): Promise<string> {
  const body = await json<{ id: string }>(
    await fetch("/api/sessions", { method: "POST" }),
    "createSession",
  );
  return body.id;
}

export async function fetchHistory(sessionId: string): Promise<HistoryMessage[]> {
  return json(await fetch(`/api/sessions/${sessionId}/messages`), "fetchHistory");
}
