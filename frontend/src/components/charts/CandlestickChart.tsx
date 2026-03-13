import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

interface HistoricalDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface Props {
  data: HistoricalDataPoint[];
}

export default function CandlestickChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <ComposedChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />

        <XAxis
          dataKey="date"
          tick={{ fontSize: 12 }}
        />

        <YAxis
          yAxisId="price"
          domain={["auto", "auto"]}
          tick={{ fontSize: 12 }}
        />

        <YAxis
          yAxisId="volume"
          orientation="right"
          hide
        />

        <Tooltip />

        {/* Price Line */}
        <Line
          yAxisId="price"
          type="monotone"
          dataKey="close"
          stroke="#2563eb"
          strokeWidth={2}
          dot={false}
        />

        {/* Volume Bars */}
        <Bar
          yAxisId="volume"
          dataKey="volume"
          fill="#94a3b8"
          opacity={0.3}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}