"use client";

import React, { useState, useEffect } from "react";
import { Search, ListFilter } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export default function BouncedEmailsPage() {
  const [bounces, setBounces] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");

  useEffect(() => {
    fetch(`${API_BASE}/bounces`)
      .then(res => res.json())
      .then(data => setBounces(data))
      .catch(err => console.error("Failed to fetch bounces", err));
  }, []);

  const filteredBounces = bounces.filter(b => {
    const matchesSearch = 
      b.email.toLowerCase().includes(searchQuery.toLowerCase()) || 
      (b.contact_name || "").toLowerCase().includes(searchQuery.toLowerCase());
      
    if (filterType === "all") return matchesSearch;
    if (filterType === "hard") return matchesSearch && b.bounce_type === "hard";
    if (filterType === "soft") return matchesSearch && b.bounce_type === "soft";
    if (filterType === "ooo") return matchesSearch && b.bounce_reason.includes("Out of Office");
    return matchesSearch;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">Suppression List</h1>
          <p className="text-zinc-500 text-sm mt-1">Manage bounced contacts and out-of-office auto-replies.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search size={14} strokeWidth={1.5} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input 
              type="text" 
              placeholder="Search email or name..." 
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="bg-zinc-950/50 border border-zinc-800 text-sm text-zinc-200 rounded-xl pl-9 pr-4 py-2 focus:outline-none focus:border-zinc-700 w-full md:w-64"
            />
          </div>
          <div className="relative">
            <ListFilter size={14} strokeWidth={1.5} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <select 
              value={filterType}
              onChange={e => setFilterType(e.target.value)}
              className="bg-zinc-950/50 border border-zinc-800 text-sm text-zinc-200 rounded-xl pl-9 pr-8 py-2 focus:outline-none focus:border-zinc-700 appearance-none cursor-pointer"
            >
              <option value="all">All Types</option>
              <option value="hard">Hard Bounces</option>
              <option value="soft">Soft Bounces</option>
              <option value="ooo">Out of Office</option>
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500 text-xs">▼</div>
          </div>
        </div>
      </div>

      <div className="bg-zinc-950/50 border border-zinc-800/60 rounded-2xl overflow-hidden mt-4">
        <table className="w-full text-left text-sm text-zinc-400">
          <thead className="bg-zinc-900/40 border-b border-zinc-800/60 text-xs uppercase text-zinc-500 font-semibold tracking-wider">
            <tr>
              <th className="px-6 py-4">Name</th>
              <th className="px-6 py-4">Email</th>
              <th className="px-6 py-4">Type</th>
              <th className="px-6 py-4 w-1/3">Reason</th>
              <th className="px-6 py-4">Date</th>
              <th className="px-6 py-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50">
            {filteredBounces.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-zinc-500 italic">No contacts found matching your filter.</td>
              </tr>
            ) : (
              filteredBounces.map((b, i) => (
                <tr key={i} className="hover:bg-zinc-900/40">
                  <td className="px-6 py-4">
                    <p className="text-zinc-200 font-medium">{b.contact_name || "Unknown"}</p>
                    {b.city && <p className="text-xs text-zinc-500">{b.city}</p>}
                  </td>
                  <td className="px-6 py-4">
                    <p className="text-zinc-300 font-medium">{b.email}</p>
                  </td>
                  <td className="px-6 py-4">
                    {b.bounce_type === 'hard' ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-red-950/50 text-red-400 text-xs font-medium border border-red-900/50">
                        Hard Bounce
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-950/50 text-amber-400 text-xs font-medium border border-amber-900/50">
                        {b.bounce_reason.includes("Out of Office") ? "Out of Office" : "Soft Bounce"}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-xs font-mono text-zinc-500">{b.bounce_reason}</td>
                  <td className="px-6 py-4">{new Date(b.date_bounced).toLocaleDateString()}</td>
                  <td className="px-6 py-4 text-xs font-semibold">
                    {b.bounce_type === 'hard' ? (
                      <span className="text-zinc-600">Suppressed (Never Email)</span>
                    ) : (
                      <span className="text-zinc-400">Retry After 7 Days</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
