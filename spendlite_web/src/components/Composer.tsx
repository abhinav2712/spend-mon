import { useState, type FormEvent } from "react";

type Props = { disabled: boolean; onSend: (text: string) => void };

export default function Composer({ disabled, onSend }: Props) {
  const [value, setValue] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    const text = value.trim();
    if (!text || disabled) return;
    setValue("");
    onSend(text);
  }

  return (
    <form onSubmit={submit} className="relative z-10 px-6 pb-6">
      <div className="glass liquid mx-auto flex max-w-3xl items-center gap-2 rounded-2xl p-2">
        <input
          className="flex-1 bg-transparent px-3 py-2 text-sm outline-none placeholder:text-[color:var(--ink-mute)] disabled:opacity-50"
          placeholder={disabled ? "Thinking…" : "Ask about your spending…"}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={disabled}
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="liquid rounded-xl px-4 py-2 text-sm font-medium text-white disabled:opacity-30"
          style={{
            background: "var(--accent)",
            boxShadow:
              "0 6px 20px var(--accent-soft), inset 0 1px 0 rgba(255,255,255,0.25)",
          }}
        >
          Send
        </button>
      </div>
    </form>
  );
}
