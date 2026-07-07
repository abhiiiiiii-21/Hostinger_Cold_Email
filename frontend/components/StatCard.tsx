import React from "react";

export function StatCard({ title, value, icon, trend }: { title: string, value: string, icon: React.ReactNode, trend?: string }) {
  return (
    <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-2xl p-6 flex flex-col justify-between group hover:border-zinc-700/80 hover:bg-zinc-900/60 transition-all duration-300 relative overflow-hidden backdrop-blur-sm shadow-sm">
      <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-zinc-700/30 to-transparent"></div>
      
      <div className="flex justify-between items-start mb-6">
        <div className="text-zinc-300 bg-zinc-800/80 p-2.5 rounded-xl border border-zinc-700/50 shadow-inner flex items-center justify-center">
          {icon}
        </div>
        {trend && (
          <span className="text-xs font-medium text-zinc-900 bg-zinc-200 px-2.5 py-1 rounded-full shadow-sm">
            {trend}
          </span>
        )}
      </div>
      <div>
        <h3 className="text-4xl font-bold text-zinc-100 tracking-tight mb-1">{value}</h3>
        <p className="text-sm font-medium text-zinc-500">{title}</p>
      </div>
    </div>
  );
}
