import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CategoryRow } from "../lib/events";
import { formatINR, titleCase } from "../lib/format";

type Props = { rows: CategoryRow[]; month?: string };

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: unknown[];
}) {
  if (!active || !payload?.length) return null;
  const row = (payload[0] as { payload: CategoryRow }).payload;
  return (
    <div
      className="rounded-xl px-3 py-2 text-xs"
      style={{
        background: "#141c2b",
        border: "1px solid var(--hairline)",
        boxShadow: "0 12px 32px rgba(0,0,0,0.55)",
      }}
    >
      <p className="font-medium" style={{ color: "var(--ink)" }}>
        {titleCase(row.category)}
      </p>
      <p style={{ color: "var(--ink-dim)" }}>
        {formatINR(row.total_inr)} · {row.count}{" "}
        {row.count === 1 ? "expense" : "expenses"}
      </p>
    </div>
  );
}

export default function CategoryChart({ rows, month }: Props) {
  const data = [...rows].sort((a, b) => b.total_inr - a.total_inr);
  const max = Math.max(...data.map((r) => r.total_inr));

  return (
    <figure className="glass rise mt-3 rounded-2xl p-4">
      <figcaption
        className="mb-3 text-xs font-medium tracking-wide"
        style={{ color: "var(--ink-dim)" }}
      >
        Spending by category{month ? ` · ${month}` : ""}
      </figcaption>
      <ResponsiveContainer width="100%" height={data.length * 38 + 8}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ left: 0, right: 64, top: 0, bottom: 0 }}
        >
          <XAxis type="number" hide domain={[0, max * 1.18]} />
          <YAxis
            type="category"
            dataKey="category"
            width={92}
            axisLine={false}
            tickLine={false}
            tick={{ fill: "var(--ink-dim)", fontSize: 12 }}
            tickFormatter={titleCase}
          />
          <Tooltip
            cursor={{ fill: "rgba(255,255,255,0.05)" }}
            content={<ChartTooltip />}
            offset={16}
            wrapperStyle={{ outline: "none", zIndex: 20 }}
          />

          <Bar
            dataKey="total_inr"
            radius={[0, 7, 7, 0]}
            barSize={16}
            isAnimationActive
          >
            {data.map((row) => (
              <Cell key={row.category} fill="var(--accent)" />
            ))}
            <LabelList
              dataKey="total_inr"
              position="right"
              offset={10}
              formatter={(v) => formatINR(Number(v ?? 0))}
              style={{
                fill: "var(--ink-dim)",
                fontSize: 11,
                fontVariantNumeric: "tabular-nums",
              }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </figure>
  );
}
