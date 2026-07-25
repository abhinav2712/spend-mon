import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function Markdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
        ul: ({ children }) => (
          <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0 marker:text-[color:var(--ink-mute)]">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0 marker:text-[color:var(--ink-mute)]">
            {children}
          </ol>
        ),
        strong: ({ children }) => (
          <strong className="font-semibold" style={{ color: "var(--ink)" }}>
            {children}
          </strong>
        ),
        table: ({ children }) => (
          <div
            className="my-3 overflow-x-auto rounded-xl border"
            style={{ borderColor: "var(--hairline)" }}
          >
            <table className="w-full border-collapse text-xs">{children}</table>
          </div>
        ),
        thead: ({ children }) => (
          <thead
            className="text-[11px] uppercase tracking-wide"
            style={{
              color: "var(--ink-mute)",
              background: "rgba(255,255,255,0.03)",
            }}
          >
            {children}
          </thead>
        ),
        th: ({ children, style }) => (
          <th style={style} className="px-3 py-2 text-left font-medium">
            {children}
          </th>
        ),
        td: ({ children, style }) => (
          <td
            style={style}
            className="border-t border-[color:var(--hairline)] px-3 py-2 tabular-nums"
          >
            {children}
          </td>
        ),
      }}
    >
      {children}
    </ReactMarkdown>
  );
}
