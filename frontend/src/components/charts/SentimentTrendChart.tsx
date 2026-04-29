import type { TooltipProps } from "recharts";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

interface SentimentData {
  date: string;
  sentimentScore: number;
}

interface Props {
  data: SentimentData[];
  range: "1D" | "1W" | "1M";
}

function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const val = payload[0].value as number;
  const isPositive = val >= 0;

  return (
    <div
      style={{
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "8px",
        padding: "10px 14px",
        boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
      }}
    >
      <p style={{ color: "#94a3b8", fontSize: "11px", marginBottom: "4px", fontFamily: "monospace" }}>
        {label}
      </p>
      <p
        style={{
          color: isPositive ? "#16a34a" : "#dc2626",
          fontSize: "20px",
          fontWeight: 700,
          fontFamily: "monospace",
          letterSpacing: "-0.5px",
        }}
      >
        {val > 0 ? "+" : ""}{val.toFixed(3)}
      </p>
      <p style={{ color: "#94a3b8", fontSize: "10px", marginTop: "2px" }}>
        {isPositive ? "▲ Bullish" : "▼ Bearish"}
      </p>
    </div>
  );
}

export default function SentimentTrendChart({ data, range }: Props) {
  const lastVal = data[data.length - 1]?.sentimentScore ?? 0;
  const avgVal = data.reduce((s, d) => s + d.sentimentScore, 0) / (data.length || 1);
  const isPositive = lastVal >= 0;
  const lineColor = isPositive ? "#16a34a" : "#dc2626";
  const gradientId = isPositive ? "gradGreen" : "gradRed";

  const formatXAxis = (value: string) => {
    if (range === "1D") return value;
    if (range === "1W") return value;
    if (range === "1M") return value;
    return value;
  };

  return (
    <div
      style={{
        background: "#ffffff",
        borderRadius: "14px",
        padding: "24px 24px 16px",
        border: "1px solid #e2e8f0",
        boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
        fontFamily: "'DM Sans', sans-serif",
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: "20px" }}>
        <p style={{ color: "#94a3b8", fontSize: "11px", textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: "6px" }}>
          Sentiment Score
        </p>
        <div style={{ display: "flex", alignItems: "baseline", gap: "12px" }}>
          <span
            style={{
              color: lineColor,
              fontSize: "36px",
              fontWeight: 700,
              fontFamily: "monospace",
              letterSpacing: "-1px",
              lineHeight: 1,
              transition: "color 0.3s",
            }}
          >
            {lastVal > 0 ? "+" : ""}{lastVal.toFixed(3)}
          </span>
          <span style={{ color: "#cbd5e1", fontSize: "13px" }}>
            avg {avgVal > 0 ? "+" : ""}{avgVal.toFixed(3)}
          </span>
        </div>
      </div>

      {/* Chart */}
      <div style={{ width: "100%", height: "220px" }}>
        <ResponsiveContainer>
          <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="gradGreen" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#16a34a" stopOpacity={0.12} />
                <stop offset="100%" stopColor="#16a34a" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradRed" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#dc2626" stopOpacity={0.1} />
                <stop offset="100%" stopColor="#dc2626" stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 6" stroke="#f1f5f9" vertical={false} />

            <XAxis
              dataKey="date"
              tickFormatter={formatXAxis}
              tick={{ fill: "#cbd5e1", fontSize: 11, fontFamily: "monospace" }}
              axisLine={false}
              tickLine={false}
              interval="preserveStartEnd"
              dy={6}
            />

            <YAxis
              domain={[-1, 1]}
              tickFormatter={(v) => (v > 0 ? `+${v.toFixed(1)}` : v.toFixed(1))}
              tick={{ fill: "#cbd5e1", fontSize: 11, fontFamily: "monospace" }}
              axisLine={false}
              tickLine={false}
              width={40}
              ticks={[-1, -0.5, 0, 0.5, 1]}
            />

            <Tooltip
              content={<CustomTooltip />}
              cursor={{ stroke: "#e2e8f0", strokeWidth: 1.5, strokeDasharray: "4 4" }}
            />

            <ReferenceLine
              y={0}
              stroke="#e2e8f0"
              strokeWidth={1.5}
            />

            <Area
              type="monotone"
              dataKey="sentimentScore"
              stroke={lineColor}
              strokeWidth={2}
              fill={`url(#${gradientId})`}
              dot={false}
              activeDot={{ r: 4, fill: lineColor, stroke: "#fff", strokeWidth: 2 }}
              isAnimationActive
              animationDuration={700}
              animationEasing="ease-out"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Footer */}
      <div style={{ display: "flex", gap: "16px", marginTop: "12px", paddingTop: "12px", borderTop: "1px solid #f1f5f9" }}>
        {[
          { color: "#16a34a", label: "Bullish > 0" },
          { color: "#dc2626", label: "Bearish < 0" },
          { color: "#e2e8f0", label: "Neutral = 0" },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <div style={{ width: "18px", height: "2px", background: color, borderRadius: "2px" }} />
            <span style={{ color: "#94a3b8", fontSize: "11px" }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}