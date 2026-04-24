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
  range: "1D" | "1W" | "1M";
}

export default function SentimentTrendChart({ data, range }: Props) {

  // Format X-axis based on range
  const formatXAxis = (value: string) => {
    if (range === "1D") return value;        // "14:00", "15:00"...
    if (range === "1W") return value;        // "Apr 17", "Apr 18"...
    if (range === "1M") return value;        // "Apr 01", "Apr 07"...
    return value;
  };

  // Format tooltip
  const formatTooltip = (value: number) => {
    return [`${value.toFixed(2)}`, "Sentiment"];
  };

  return (
    <div className="w-full h-80">
      <ResponsiveContainer>
        <LineChart data={data}>

          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

          <XAxis
            dataKey="date"
            tickFormatter={formatXAxis}
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
          />

          <YAxis
            domain={[-1, 1]}
            tickFormatter={(val) => val.toFixed(1)}
            tick={{ fontSize: 12 }}
          />

          <Tooltip formatter={formatTooltip} />

          <Line
            type="monotone"
            dataKey="sentimentScore"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={range === "1D"}       // dots only for hourly (small dataset)
            activeDot={{ r: 5 }}
          />

        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}