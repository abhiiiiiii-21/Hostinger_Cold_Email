"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Send, BarChart3, Users, Play } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [backendStatus, setBackendStatus] = useState<"offline" | "online" | "error">("offline");

  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`${API_BASE}/state`)
        .then(res => {
          if (!res.ok) throw new Error("Network response was not ok");
          return res.json();
        })
        .then(data => {
          setBackendStatus(data.failedList?.length > 0 ? "error" : "online");
        })
        .catch(() => {
          setBackendStatus("offline");
        });
    }, 5000); // Check status every 5s globally to save resources
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen w-full overflow-hidden bg-[#0c0c0e] text-zinc-300 flex flex-col font-sans selection:bg-zinc-200 selection:text-zinc-900">
      
      {/* TOP HEADER */}
      <header className="h-16 flex items-center justify-between px-8 bg-zinc-950/30 backdrop-blur-md border-b border-zinc-800/60 sticky top-0 z-10 shrink-0">
        <div className="flex items-center gap-3 text-zinc-100 font-bold text-lg tracking-tight">
          <div className="w-8 h-8 bg-zinc-200 rounded-md flex items-center justify-center text-zinc-900 shadow-sm">
            <Send size={18} />
          </div>
          <span>Cold Emailing</span>
        </div>
        
        <div className="flex items-center gap-4">
          <span className={`text-xs font-medium px-3 py-1.5 rounded-md flex items-center gap-2 border transition-colors duration-300 ${
            backendStatus === "online" 
              ? "bg-emerald-950/20 border-emerald-900/40 text-emerald-400" 
              : backendStatus === "error"
              ? "bg-red-950/20 border-red-900/40 text-red-400"
              : "bg-zinc-900/50 border-zinc-800 text-zinc-500"
          }`}>
            <div className={`w-2 h-2 rounded-full ${backendStatus !== "offline" ? "animate-pulse" : ""} ${
              backendStatus === "online" ? "bg-emerald-500" : backendStatus === "error" ? "bg-red-500" : "bg-zinc-600"
            }`}></div>
            {backendStatus === "online" ? "System Online" : backendStatus === "error" ? "System Error" : "System Offline"}
          </span>
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-zinc-700 to-zinc-500 flex items-center justify-center text-white font-bold text-sm shadow-inner cursor-pointer hover:opacity-80 transition">
            W
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* SIDEBAR NAVIGATION */}
        <aside className="w-[240px] border-r border-zinc-800/60 bg-zinc-950/20 overflow-y-auto hidden lg:flex flex-col shrink-0 custom-scrollbar">
          <div className="p-4 flex flex-col gap-2 mt-4">
            <Link 
              href="/"
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition ${pathname === "/" ? "bg-zinc-900 text-zinc-100 shadow-sm" : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/40"}`}
            >
              <BarChart3 size={18} />
              <span className="font-medium text-sm">Dashboard</span>
            </Link>
            <Link 
              href="/automation"
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition ${pathname === "/automation" ? "bg-zinc-900 text-zinc-100 shadow-sm" : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/40"}`}
            >
              <Play size={18} />
              <span className="font-medium text-sm">Automation</span>
            </Link>
            <Link 
              href="/history"
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition ${pathname === "/history" ? "bg-zinc-900 text-zinc-100 shadow-sm" : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/40"}`}
            >
              <Users size={18} />
              <span className="font-medium text-sm">Campaign History</span>
            </Link>
          </div>
        </aside>

        {/* MAIN CONTENT AREA */}
        <main className="flex-1 overflow-auto p-8 w-full relative custom-scrollbar">
          <div className="max-w-[1400px] mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
