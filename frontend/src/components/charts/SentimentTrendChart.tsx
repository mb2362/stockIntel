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
}

export default function SentimentTrendChart({ data }: Props) {
  return (
    <div className="w-full h-80">
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis dataKey="date" />
          <YAxis domain={[-1, 1]} />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="sentimentScore"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}