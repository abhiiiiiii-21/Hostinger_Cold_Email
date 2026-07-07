"use client";

import React, { useState, useEffect } from "react";
import { 
  Mails, MousePointerClick, MessageSquareReply, LineChart, 
  RefreshCw, MailWarning, MailX 
} from "lucide-react";
import { StatCard } from "@/components/StatCard";
import { TrendChart } from "@/components/TrendChart";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

// ── Toggle: set to false to use live API data ──
const USE_MOCK_DATA = false;

const MOCK_DATA = {
  today: 42, yesterday: 31, month: 847,
  today_opens: 18, yesterday_opens: 14, month_opens: 412,
  total_replies: 23, reply_rate: 8.2,
  hard_bounce_rate: 1.8, soft_bounce_rate: 3.4,
};
// ────────────────────────────────────────────────

export default function DashboardPage() {
  const [stats, setStats] = useState({ 
    today: 0, yesterday: 0, month: 0, 
    today_opens: 0, yesterday_opens: 0, month_opens: 0,
    total_replies: 0, reply_rate: 0,
    hard_bounce_rate: 0, soft_bounce_rate: 0
  });
  const [syncing, setSyncing] = useState(false);

  const fetchDashboardData = () => {
    if (USE_MOCK_DATA) {
      setStats(MOCK_DATA);
      return;
    }
    fetch(`${API_BASE}/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Failed to fetch stats", err));
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleSyncReplies = async () => {
    setSyncing(true);
    try {
      const res = await fetch(`${API_BASE}/sync-replies`, { method: "POST" });
      const data = await res.json();
      if (data.status === "success") {
        alert(`Sync complete! Found ${data.new_replies} new replies.`);
        fetchDashboardData();
      } else {
        alert(`Error syncing: ${data.message}`);
      }
    } catch (err) {
      alert("Error syncing replies.");
    }
    setSyncing(false);
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">Dashboard Overview</h1>
          <p className="text-zinc-500 text-sm mt-1">High-level metrics for your cold email campaigns.</p>
        </div>
        <button 
          onClick={handleSyncReplies}
          disabled={syncing}
          className="py-2.5 px-4 rounded-xl font-medium text-sm flex items-center gap-2 transition-all duration-300 bg-zinc-900/50 border border-zinc-800 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100 disabled:opacity-50"
        >
          <RefreshCw size={14} strokeWidth={2.5} className={syncing ? "animate-spin" : ""} />
          {syncing ? "Syncing IMAP..." : "Sync Replies"}
        </button>
      </div>

      {/* ── Section 1: Today ── */}
      <div className="space-y-3">
        <p className="text-xs text-zinc-500 uppercase tracking-widest font-semibold">Today</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <StatCard title="Sent Today" value={stats.today.toString()} icon={<Mails size={20} strokeWidth={1.75} className="text-zinc-400" />} />
          <StatCard title="Today's Opens" value={`${stats.today_opens} / ${stats.today}`} trend={stats.today > 0 ? `${Math.round((stats.today_opens / stats.today) * 100)}%` : "0%"} icon={<MousePointerClick size={20} strokeWidth={1.75} className="text-zinc-400" />} />
        </div>
      </div>

      {/* ── Section 2: Yesterday ── */}
      <div className="space-y-3">
        <p className="text-xs text-zinc-500 uppercase tracking-widest font-semibold">Yesterday</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <StatCard title="Sent Yesterday" value={stats.yesterday.toString()} icon={<Mails size={20} strokeWidth={1.75} className="text-zinc-400" />} />
          <StatCard title="Yesterday's Opens" value={`${stats.yesterday_opens} / ${stats.yesterday}`} trend={stats.yesterday > 0 ? `${Math.round((stats.yesterday_opens / stats.yesterday) * 100)}%` : "0%"} icon={<MousePointerClick size={20} strokeWidth={1.75} className="text-zinc-400" />} />
        </div>
      </div>

      {/* ── Section 3: This Month ── */}
      <div className="space-y-3">
        <p className="text-xs text-zinc-500 uppercase tracking-widest font-semibold">This Month</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard title="Monthly Volume" value={stats.month.toString()} icon={<LineChart size={20} strokeWidth={1.75} className="text-zinc-400" />} />
          <StatCard title="Monthly Open Rate" value={(stats.month - 172) > 0 ? `${Math.round((stats.month_opens / (stats.month - 172)) * 100)}%` : "0%"} icon={<MousePointerClick size={20} strokeWidth={1.75} className="text-zinc-400" />} />
          <StatCard title="Total Replies" value={stats.total_replies.toString()} trend={`${stats.reply_rate}% rate`} icon={<MessageSquareReply size={20} strokeWidth={1.75} className="text-zinc-400" />} />
        </div>
      </div>

      {/* ── Section 4: Deliverability ── */}
      <div className="space-y-3">
        <p className="text-xs text-zinc-500 uppercase tracking-widest font-semibold">Deliverability</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <StatCard title="Hard Bounces" value={`${stats.hard_bounce_rate}%`} icon={<MailX size={20} strokeWidth={1.75} className="text-red-400" />} />
          <StatCard title="Soft Bounces" value={`${stats.soft_bounce_rate}%`} icon={<MailWarning size={20} strokeWidth={1.75} className="text-amber-400" />} />
        </div>
      </div>

      <TrendChart />

    </div>
  );
}