import type { AgentEvent } from "./events";

export type ToolActivity = {
  callId: string;
  name: string;
  data?: unknown;
  status: "running" | "done";
};

export type ChatMessage =
  | { role: "user"; content: string }
  | {
      role: "assistant";
      content: string;
      tools: ToolActivity[];
      streaming: boolean;
      variant?: "normal" | "guardrail" | "error";
    };

export function applyEvent(messages: ChatMessage[], event: AgentEvent): ChatMessage[] {
  const last = messages[messages.length - 1];
  if (!last || last.role !== "assistant") return messages;
  const head = messages.slice(0, -1);

  switch (event.type) {
    case "delta":
      return [...head, { ...last, content: last.content + event.text }];

    case "tool_call":
      return [
        ...head,
        {
          ...last,
          tools: [...last.tools, { callId: event.call_id, name: event.name, status: "running" }],
        },
      ];

    case "tool_result":
      return [
        ...head,
        {
          ...last,
          tools: last.tools.map((t) =>
            t.callId === event.call_id ? { ...t, status: "done" as const, data: event.data } : t,
          ),
        },
      ];

    case "guardrail_triggered":
      return [
        ...head,
        { ...last, content: event.message, tools: [], streaming: false, variant: "guardrail" },
      ];

    case "error":
      return [
        ...head,
        {
          ...last,
          content: `Something went wrong: ${event.message}`,
          streaming: false,
          variant: "error",
        },
      ];

    case "done":
      return [...head, { ...last, streaming: false }];
  }
}
