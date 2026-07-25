type Props = { streaming: boolean };

export default function Header({ streaming }: Props) {
  return (
    <header className="glass liquid mx-4 mt-4 flex items-center gap-3 rounded-2xl px-4 py-3">
      <span
        className="grid h-9 w-9 shrink-0 place-items-center rounded-xl"
        style={{
          background: "linear-gradient(145deg, #7cadff 0%, #2f6bff 100%)",
          boxShadow:
            "0 6px 18px var(--accent-soft), inset 0 1px 0 rgba(255,255,255,0.4)",
        }}
      >
        <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
          <rect
            x="2"
            y="10"
            width="3"
            height="6"
            rx="1.5"
            fill="#fff"
            fillOpacity="0.7"
          />
          <rect x="7.5" y="6" width="3" height="10" rx="1.5" fill="#fff" />
          <rect
            x="13"
            y="2.5"
            width="3"
            height="13.5"
            rx="1.5"
            fill="#fff"
            fillOpacity="0.85"
          />
        </svg>
      </span>

      <div className="min-w-0">
        <h1 className="bg-gradient-to-r from-white to-[#9fc2ff] bg-clip-text text-[15px] font-semibold leading-tight tracking-tight text-transparent">
          SpendLite
        </h1>
        <p
          className="truncate text-[11px]"
          style={{ color: "var(--ink-mute)" }}
        >
          Your expenses, answered from your own records
        </p>
      </div>

      <span
        className="glass-flat ml-auto hidden shrink-0 items-center gap-2 rounded-full px-3 py-1.5 text-[11px] sm:inline-flex"
        style={{
          color: streaming ? "var(--ink)" : "var(--ink-mute)",
          borderColor: streaming ? "var(--accent-line)" : "var(--hairline)",
          boxShadow: streaming ? "0 0 18px var(--accent-soft)" : undefined,
        }}
      >
        <span
          className={`h-1.5 w-1.5 rounded-full ${streaming ? "breathe" : ""}`}
          style={{ background: streaming ? "var(--accent)" : "#3ecf8e" }}
        />
        {streaming ? "Thinking" : "Ready"}
      </span>
    </header>
  );
}
