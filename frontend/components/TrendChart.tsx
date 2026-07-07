"use client";

import React, { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

const TREND_DAYS = 30; // Adjust this to change the day range

interface DailyData {
  date: string;
  sent: number;
  opens: number;
  replies: number;
}

function formatDateLabel(isoDate: string) {
  const d = new Date(isoDate + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-zinc-900 border border-zinc-700/60 rounded-xl px-4 py-3 shadow-xl">
      <p className="text-zinc-400 text-xs font-medium mb-2">{formatDateLabel(label)}</p>
      {payload.map((entry: any, i: number) => (
        <div key={i} className="flex items-center gap-2 text-sm">
          <div className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
          <span className="text-zinc-400">{entry.name}:</span>
          <span className="text-zinc-100 font-semibold">{entry.value}</span>
        </div>
      ))}
    </div>
  );
}

export function TrendChart() {
  const [data, setData] = useState<DailyData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/trend?days=${TREND_DAYS}`)
      .then((res) => res.json())
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-2xl p-6 relative overflow-hidden backdrop-blur-sm shadow-sm group hover:border-zinc-700/80 hover:bg-zinc-900/60 transition-all duration-300">
      <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-zinc-700/30 to-transparent" />

      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-lg font-semibold text-zinc-100 tracking-tight">
            Campaign Trend
          </h3>
          <p className="text-zinc-500 text-xs mt-0.5">
            Last {TREND_DAYS} days performance
          </p>
        </div>
      </div>

      {loading ? (
        <div className="h-[300px] flex items-center justify-center">
          <div className="w-5 h-5 border-2 border-zinc-700 border-t-zinc-400 rounded-full animate-spin" />
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart
            data={data}
            margin={{ top: 5, right: 10, left: -10, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(113, 113, 122, 0.15)"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              tickFormatter={formatDateLabel}
              tick={{ fill: "#71717a", fontSize: 11 }}
              axisLine={{ stroke: "rgba(113, 113, 122, 0.2)" }}
              tickLine={false}
              interval="preserveStartEnd"
              minTickGap={40}
            />
            <YAxis
              tick={{ fill: "#71717a", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ paddingTop: 16, fontSize: 12 }}
              formatter={(value: string) => (
                <span className="text-zinc-400 ml-1">{value}</span>
              )}
            />
            <Line
              type="monotone"
              dataKey="sent"
              name="Sent"
              stroke="#a1a1aa"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0, fill: "#a1a1aa" }}
            />
            <Line
              type="monotone"
              dataKey="opens"
              name="Opens"
              stroke="#60a5fa"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0, fill: "#60a5fa" }}
            />
            <Line
              type="monotone"
              dataKey="replies"
              name="Replies"
              stroke="#4ade80"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0, fill: "#4ade80" }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
