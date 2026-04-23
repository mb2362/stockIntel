import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

interface SentimentData {
  date: string;
  sentimentScore: number; // -1 to +1
}

interface Props {
  data: SentimentData[];
  range: "7D" | "1M" | "1Y" | "5Y";
}

export default function SentimentTrendChart({ data, range }: Props) {
  
  // Format X-axis based on range
  const formatXAxis = (value: string) => {
    if (range === "1M") return value.replace("Day ", "");
    if (range === "1Y") return value; // M1, M2...
    if (range === "5Y") return value; // Y1, Y2...
    return value; // Mon, Tue...
  };

  // Format tooltip
  const formatTooltip = (value: number) => {
    return [`${value.toFixed(2)}`, "Sentiment"];
  };

  return (
    <div className="w-full h-80">
      <ResponsiveContainer>
        <LineChart data={data}>
          {/* Grid */}
          <CartesianGrid strokeDasharray="3 3" />

          {/* X Axis */}
          <XAxis
            dataKey="date"
            tickFormatter={formatXAxis}
            tick={{ fontSize: 12 }}
          />

          {/* Y Axis */}
          <YAxis
            domain={[-1, 1]}
            tickFormatter={(val) => val.toFixed(1)}
          />

          {/* Tooltip */}
          <Tooltip formatter={formatTooltip} />

          {/* Line */}
          <Line
            type="monotone"
            dataKey="sentimentScore"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={range === "7D"} // dots only for small dataset
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}