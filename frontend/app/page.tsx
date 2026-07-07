"use client";

import React, { useState, useEffect } from "react";
import { CheckCircle2, Play, Users, BarChart3 } from "lucide-react";
import { StatCard } from "@/components/StatCard";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export default function DashboardPage() {
  const [stats, setStats] = useState({ today: 0, yesterday: 0, month: 0, today_opens: 0, yesterday_opens: 0, month_opens: 0 });

  useEffect(() => {
    fetch(`${API_BASE}/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Failed to fetch stats", err));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">Dashboard Overview</h1>
        <p className="text-zinc-500 text-sm mt-1">High-level metrics for your cold email campaigns.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard title="Sent Today" value={stats.today.toString()} icon={<CheckCircle2 size={20} className="text-zinc-400" />} />
        <StatCard title="Today's Opens" value={`${stats.today_opens} / ${stats.today}`} trend={stats.today > 0 ? `${Math.round((stats.today_opens / stats.today) * 100)}%` : "0%"} icon={<Play size={20} className="text-zinc-400" />} />
        <StatCard title="Sent Yesterday" value={stats.yesterday.toString()} icon={<Users size={20} className="text-zinc-400" />} />
        <StatCard title="Yesterday's Opens" value={`${stats.yesterday_opens} / ${stats.yesterday}`} trend={stats.yesterday > 0 ? `${Math.round((stats.yesterday_opens / stats.yesterday) * 100)}%` : "0%"} icon={<Play size={20} className="text-zinc-400" />} />
        <StatCard title="Monthly Volume" value={stats.month.toString()} icon={<BarChart3 size={20} className="text-zinc-400" />} />
        <StatCard title="Monthly Open Rate" value={stats.month > 0 ? `${Math.round((stats.month_opens / stats.month) * 100)}%` : "0%"} icon={<Play size={20} className="text-zinc-400" />} />
      </div>
    </div>
  );
}