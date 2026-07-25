import { useEffect, useRef } from "react";
import type { ChatMessage } from "../lib/chat";
import MessageBubble from "./MessageBubble";

export default function MessageList({ messages }: { messages: ChatMessage[] }) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="relative z-10 flex-1 overflow-y-auto px-6 py-6">
      <div className="mx-auto flex max-w-3xl flex-col gap-5">
        {messages.length === 0 && (
          <div className="mt-16 text-center">
            <p className="text-sm" style={{ color: "var(--ink-dim)" }}>
              Ask about your recorded expenses
            </p>
            <p className="mt-1 text-xs" style={{ color: "var(--ink-mute)" }}>
              Try “Break down my June 2026 spending by category”
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
