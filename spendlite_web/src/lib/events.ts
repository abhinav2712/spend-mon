export type AgentEvent =
  | { type: "delta"; text: string }
  | { type: "tool_call"; name: string; call_id: string }
  | { type: "tool_result"; name: string; call_id: string; data: unknown }
  | { type: "guardrail_triggered"; message: string }
  | { type: "done"; session_id: string }
  | { type: "error"; message: string };

export type SessionSummary = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type HistoryMessage = { role: "user" | "assistant"; content: string };

export type CategoryRow = { category: string; total_inr: number; count: number };

export function isCategorySummary(data: unknown): data is CategoryRow[] {
  return (
    Array.isArray(data) &&
    data.length > 0 &&
    data.every(
      (r) =>
        typeof r === "object" &&
        r !== null &&
        typeof (r as CategoryRow).category === "string" &&
        typeof (r as CategoryRow).total_inr === "number",
    )
  );
}
