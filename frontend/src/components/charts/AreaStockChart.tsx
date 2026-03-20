import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { formatPrice, formatLargeNumber } from "../../utils/formatters";

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

// Custom Tooltip component for a clean, premium look
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload as HistoricalDataPoint;
    
    return (
      <div className="bg-gray-900/95 dark:bg-gray-800/95 backdrop-blur-md border border-gray-700 dark:border-gray-600 p-4 rounded-xl shadow-2xl text-sm min-w-[200px]">
        <p className="font-semibold text-gray-200 mb-2 border-b border-gray-700 pb-2">
          {data.date}
        </p>
        <div className="space-y-1.5">
          <div className="flex justify-between items-center text-gray-300">
            <span className="text-gray-400">Close:</span>
            <span className="font-bold text-white">{formatPrice(data.close)}</span>
          </div>
          <div className="flex justify-between items-center text-gray-300">
            <span className="text-gray-400">Open:</span>
            <span className="font-medium">{formatPrice(data.open)}</span>
          </div>
          <div className="flex justify-between items-center text-gray-300">
            <span className="text-gray-400">High:</span>
            <span className="font-medium text-success-400">{formatPrice(data.high)}</span>
          </div>
          <div className="flex justify-between items-center text-gray-300">
            <span className="text-gray-400">Low:</span>
            <span className="font-medium text-danger-400">{formatPrice(data.low)}</span>
          </div>
          {data.volume && (
             <div className="flex justify-between items-center text-gray-300 mt-2 pt-1 border-t border-gray-700">
              <span className="text-gray-400">Volume:</span>
              <span className="font-medium">{formatLargeNumber(data.volume)}</span>
            </div>
          )}
        </div>
      </div>
    );
  }
  return null;
};

export default function AreaStockChart({ data }: Props) {
  if (!data || data.length === 0) return null;

  const firstPrice = data[0].close;
  const lastPrice = data[data.length - 1].close;
  const isPositiveTrend = lastPrice >= firstPrice;

  // Colors based on trend
  const strokeColor = isPositiveTrend ? "#10b981" : "#ef4444"; // emerald-500 : red-500
  const stopColor = isPositiveTrend ? "#10b981" : "#ef4444";

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ComposedChart data={data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={stopColor} stopOpacity={0.4} />
            <stop offset="95%" stopColor={stopColor} stopOpacity={0.0} />
          </linearGradient>
        </defs>

        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" opacity={0.2} />

        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: '#6b7280' }}
          tickLine={false}
          axisLine={false}
          minTickGap={30}
          dy={10}
        />

        <YAxis
          yAxisId="price"
          domain={["auto", "auto"]}
          tick={{ fontSize: 11, fill: '#6b7280' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(val) => `$${val}`}
        />

        <YAxis
          yAxisId="volume"
          orientation="right"
          hide
        />

        <Tooltip
          content={<CustomTooltip />}
          cursor={{ stroke: '#6b7280', strokeWidth: 1, strokeDasharray: '4 4' }}
          isAnimationActive={false}
        />

        {/* Volume Bars */}
        <Bar
          yAxisId="volume"
          dataKey="volume"
          fill="#94a3b8"
          opacity={0.15}
          maxBarSize={40}
        />

        {/* Mountain Area */}
        <Area
          yAxisId="price"
          type="monotone"
          dataKey="close"
          stroke={strokeColor}
          strokeWidth={3}
          fillOpacity={1}
          fill="url(#colorClose)"
          activeDot={{ r: 6, fill: strokeColor, stroke: '#1e293b', strokeWidth: 2 }}
        />
        
      </ComposedChart>
    </ResponsiveContainer>
  );
}
