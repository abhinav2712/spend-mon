import type { ToolActivity } from "../lib/chat";

const LABELS: Record<string, string> = {
  get_available_months: "Checking available months",
  list_categories: "Listing categories",
  get_expenses: "Fetching expenses",
  get_category_summary: "Summarising by category",
};

export default function ToolChip({ tool }: { tool: ToolActivity }) {
  const running = tool.status === "running";
  return (
    <span
      className="glass-flat liquid inline-flex items-center gap-2 rounded-full px-3 py-1 text-[11px]"
      style={{
        color: running ? "var(--ink)" : "var(--ink-mute)",
        borderColor: running ? "var(--accent-line)" : "var(--hairline)",
        boxShadow: running ? "0 0 18px var(--accent-soft)" : undefined,
      }}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${running ? "breathe" : ""}`}
        style={{ background: running ? "var(--accent)" : "var(--ink-mute)" }}
      />
      {LABELS[tool.name] ?? tool.name}
    </span>
  );
}
