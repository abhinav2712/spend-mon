import type { SessionSummary } from "../lib/events";

type Props = {
  sessions: SessionSummary[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
};

export default function Sidebar({
  sessions,
  activeId,
  onSelect,
  onNew,
}: Props) {
  return (
    <aside className="glass relative z-10 m-4 mr-0 flex w-64 shrink-0 flex-col rounded-3xl p-3">
      <button
        onClick={onNew}
        className="liquid glass-flat mb-3 rounded-2xl px-3 py-2.5 text-sm font-medium"
      >
        + New chat
      </button>

      <nav className="flex-1 space-y-1 overflow-y-auto">
        {sessions.length === 0 && (
          <p className="px-3 py-2 text-xs" style={{ color: "var(--ink-mute)" }}>
            No conversations yet
          </p>
        )}
        {sessions.map((s) => {
          const active = s.id === activeId;
          return (
            <button
              key={s.id}
              onClick={() => onSelect(s.id)}
              className="liquid block w-full truncate rounded-xl px-3 py-2 text-left text-sm"
              style={{
                background: active ? "var(--accent-soft)" : "transparent",
                color: active ? "var(--ink)" : "var(--ink-dim)",
                boxShadow: active
                  ? "inset 0 0 0 1px var(--accent-line)"
                  : undefined,
              }}
            >
              {s.title}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
