import type { ChatMessage } from "../lib/chat";
import type { CategoryRow } from "../lib/events";
import { isCategorySummary } from "../lib/events";
import CategoryChart from "./CategoryChart";
import Markdown from "./Markdown";
import ToolChip from "./ToolChip";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return (
      <div
        className="rise liquid max-w-[78%] self-end rounded-2xl rounded-br-md px-4 py-2.5 text-sm text-white"
        style={{
          background: "var(--accent)",
          boxShadow:
            "0 8px 26px var(--accent-soft), inset 0 1px 0 rgba(255,255,255,0.22)",
        }}
      >
        {message.content}
      </div>
    );
  }

  const summary = message.tools.find(
    (t) =>
      t.name === "get_category_summary" &&
      t.status === "done" &&
      isCategorySummary(t.data),
  );

  const accent =
    message.variant === "guardrail"
      ? "rgba(245, 190, 90, 0.45)"
      : message.variant === "error"
        ? "rgba(245, 110, 110, 0.45)"
        : undefined;

  return (
    <div className="rise max-w-[88%] self-start">
      {message.tools.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-1.5">
          {message.tools.map((t) => (
            <ToolChip key={t.callId} tool={t} />
          ))}
        </div>
      )}

      {summary && <CategoryChart rows={summary.data as CategoryRow[]} />}

      {(message.content || message.streaming) && (
        <div
          className="glass mt-3 rounded-2xl rounded-bl-md px-4 py-3 text-sm leading-relaxed"
          style={{ borderColor: accent, color: "var(--ink)" }}
        >
          {message.content && <Markdown>{message.content}</Markdown>}
          {message.streaming && !message.content && (
            <span className="breathe" style={{ color: "var(--ink-mute)" }}>
              Thinking…
            </span>
          )}
          {message.streaming && message.content && (
            <span
              className="breathe ml-1 inline-block h-3.5 w-[3px] translate-y-0.5 rounded-full"
              style={{ background: "var(--accent)" }}
            />
          )}
        </div>
      )}
    </div>
  );
}
