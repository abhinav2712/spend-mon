import { useEffect, useRef, useState } from "react";
import Composer from "./components/Composer";
import MessageList from "./components/MessageList";
import Sidebar from "./components/Sidebar";
import { createSession, fetchHistory, listSessions } from "./lib/api";
import { applyEvent, type ChatMessage } from "./lib/chat";
import type { HistoryMessage, SessionSummary } from "./lib/events";
import { streamChat } from "./lib/stream";

function toChatMessage(m: HistoryMessage): ChatMessage {
  return m.role === "user"
    ? { role: "user", content: m.content }
    : { role: "assistant", content: m.content, tools: [], streaming: false };
}

export default function App() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const bootstrapped = useRef(false);

  useEffect(() => {
    if (bootstrapped.current) return; // StrictMode invokes effects twice in dev
    bootstrapped.current = true;
    void bootstrap();
  }, []);

  async function bootstrap() {
    const list = await listSessions();
    setSessions(list);
    if (list.length > 0) await selectSession(list[0].id);
    else await startNew();
  }

  async function selectSession(id: string) {
    setSessionId(id);
    const history = await fetchHistory(id);
    setMessages(history.map(toChatMessage));
  }

  async function startNew() {
    setSessionId(await createSession());
    setMessages([]);
  }

  async function send(text: string) {
    if (!sessionId) return;
    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
      { role: "assistant", content: "", tools: [], streaming: true },
    ]);
    setStreaming(true);
    try {
      for await (const event of streamChat(sessionId, text)) {
        setMessages((prev) => applyEvent(prev, event));
      }
      setSessions(await listSessions());
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div className="relative flex h-screen">
      <Sidebar
        sessions={sessions}
        activeId={sessionId}
        onSelect={selectSession}
        onNew={startNew}
      />
      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        <header className="px-6 pt-6 pb-1">
          <h1 className="text-base font-semibold tracking-tight">SpendLite</h1>
          <p className="text-xs" style={{ color: "var(--ink-mute)" }}>
            Your expenses, answered from your own records
          </p>
        </header>
        <MessageList messages={messages} />
        <Composer disabled={streaming || !sessionId} onSend={send} />
      </div>
    </div>
  );
}

