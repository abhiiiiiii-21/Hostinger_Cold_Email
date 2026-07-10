"use client";

import React, { useState, useEffect } from "react";
import { Send, CheckCircle2, AlertCircle, RefreshCw, Trash2, Link2 } from "lucide-react";
import { useAuth } from "@clerk/nextjs";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export default function InboxPage() {
  const { getToken } = useAuth();
  
  // Tracking State
  const [trackingData, setTrackingData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedBodyId, setExpandedBodyId] = useState<string | null>(null);
  
  const fetchTracking = async () => {
    setIsLoading(true);
    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/single-sends/tracking`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setTrackingData(data);
      }
    } catch (err) {
      console.error("Failed to fetch tracking data", err);
    }
    setIsLoading(false);
  };

  const handleDelete = async (trackingId: string) => {
    if (!window.confirm("Are you sure you want to delete this email record?")) return;
    
    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/single-sends/${trackingId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      if (res.ok) {
        fetchTracking();
      } else {
        alert("Failed to delete the record");
      }
    } catch (err) {
      console.error("Failed to delete record", err);
    }
  };

  useEffect(() => {
    fetchTracking();
    const interval = setInterval(fetchTracking, 30000);

    const handleRefresh = () => {
      fetchTracking();
    };
    window.addEventListener("refresh-inbox-tracking", handleRefresh);

    return () => {
      clearInterval(interval);
      window.removeEventListener("refresh-inbox-tracking", handleRefresh);
    };
  }, []);

  return (
    <div className="flex flex-col font-sans -mx-4">
      {/* UNIFIED STICKY HEADER */}
      <div className="sticky top-[-32px] z-30 bg-[#0c0c0e] -mt-8 pt-10 flex flex-col">
        {/* Main Header */}
        <div className="shrink-0 flex items-center justify-between px-10 py-5 border-b border-zinc-800/60">
          <div>
            <h1 className="text-2xl font-semibold text-zinc-100 tracking-tight">Sent</h1>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={fetchTracking}
              disabled={isLoading}
              className="text-zinc-400 hover:text-zinc-200 transition cursor-pointer flex items-center justify-center p-2 rounded-full hover:bg-zinc-800/50"
              title="Refresh Tracking Data"
            >
              <RefreshCw size={16} className={isLoading ? "animate-spin" : ""} />
            </button>
          </div>
        </div>

        {/* List Header */}
        <div className="flex items-center px-10 py-3 text-[11px] font-semibold text-zinc-500 uppercase tracking-wider border-b border-zinc-800/60">
          <div className="w-[320px] shrink-0 pr-4">Email</div>
          <div className="flex-1 pr-4">Subject</div>
          <div className="w-32 shrink-0 mr-6">Links</div>
          <div className="w-20 shrink-0 text-right">Date</div>
        </div>
      </div>

      {/* CONTENT LIST */}
      <div className="flex-1 min-h-0">
        {trackingData.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-zinc-500 space-y-3 mt-20">
            <Send size={32} className="opacity-20" />
            <p className="text-sm font-medium">No sent emails yet.</p>
          </div>
        ) : (
          <div className="flex flex-col">
            {trackingData.map(track => {
              // Format Date
              const sentDate = new Date(track.sent_at);
              const today = new Date();
              const isToday = sentDate.getDate() === today.getDate() && sentDate.getMonth() === today.getMonth() && sentDate.getFullYear() === today.getFullYear();
              const displayDate = isToday 
                ? sentDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
                : sentDate.toLocaleDateString([], { month: 'short', day: 'numeric' });

              const isExpanded = expandedBodyId === track.tracking_id;

              return (
                <div key={track.tracking_id} className="flex flex-col border-b border-zinc-800/20 transition-colors">
                  {/* ROW SUMMARY */}
                  <div 
                    onClick={() => setExpandedBodyId(isExpanded ? null : track.tracking_id)}
                    className={`group flex items-center px-10 py-3 cursor-pointer transition-colors text-[13px] ${isExpanded ? 'bg-zinc-800/40' : 'hover:bg-zinc-800/30'}`}
                  >
                    {/* Recipient */}
                    <div className="w-[320px] shrink-0 text-zinc-300 truncate pr-4">
                      {track.email}
                    </div>

                    {/* Subject */}
                    <div className="flex-1 truncate text-zinc-300 font-medium pr-4">
                      <span className="truncate">{track.email_subject || "No Subject"}</span>
                    </div>

                    {/* Tracking Badges */}
                    <div className="flex items-center gap-3 shrink-0 mr-6 w-32">
                      {track.open_count > 0 ? (
                        <span className="text-emerald-400/90 flex items-center gap-1.5" title={`Opened ${track.open_count} times`}>
                          <CheckCircle2 size={14} /> 
                          <span className="text-[11px] font-medium">{track.open_count}</span>
                        </span>
                      ) : (
                        <span className="text-zinc-700 flex items-center gap-1" title="Unopened">
                          <AlertCircle size={14} />
                        </span>
                      )}
                      {track.clicks && track.clicks.length > 0 && (
                        <span className="text-blue-400/90 flex items-center gap-1.5" title={`${track.clicks.length} link clicks`}>
                          <Link2 size={14} />
                          <span className="text-[11px] font-medium">{track.clicks.length}</span>
                        </span>
                      )}
                    </div>

                    {/* Date */}
                    <div className="w-20 shrink-0 text-right flex items-center justify-end font-medium">
                      <span className="text-zinc-500">
                        {displayDate}
                      </span>
                    </div>
                  </div>

                  {/* ACCORDION CONTENT */}
                  {isExpanded && (
                    <div className="flex bg-zinc-900/30 p-10 gap-10 animate-in slide-in-from-top-2 fade-in duration-200 border-t border-zinc-800/40">
                      {/* Left: Email Body */}
                      <div className="flex-1 bg-zinc-950/80 border border-zinc-800/60 rounded-xl p-5 overflow-hidden flex flex-col">
                        <div className="flex items-center justify-between border-b border-zinc-800/60 pb-3 mb-3 shrink-0">
                          <h3 className="text-zinc-300 font-semibold text-sm">Message Details</h3>
                        </div>
                        <div className="flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar pr-4 max-h-[300px]">
                          {track.email_body ? (
                            <div 
                              className="text-zinc-400 text-[13px] leading-relaxed break-words [&>p]:mb-3 [&>p:last-child]:mb-0 [&_a]:text-blue-400 [&_a]:hover:underline"
                              dangerouslySetInnerHTML={{ __html: track.email_body.replace(/&nbsp;/g, ' ') }} 
                            />
                          ) : (
                            <span className="text-zinc-600 text-sm">No message stored</span>
                          )}
                        </div>
                      </div>

                      {/* Right: Metadata & Tracking Timeline */}
                      <div className="w-[320px] flex flex-col gap-6 shrink-0 bg-zinc-950/80 border border-zinc-800/60 rounded-xl p-5">
                        {/* Recipient Details */}
                        <div>
                          <h3 className="text-zinc-300 font-semibold text-sm border-b border-zinc-800/60 pb-3 mb-3">Recipient Info</h3>
                          <div className="flex flex-col gap-3 text-sm text-zinc-400">
                            <div className="flex flex-col gap-1">
                              <span className="text-zinc-500 text-[11px] uppercase tracking-wider font-semibold">Name</span>
                              <span className="text-zinc-200 font-medium">{track.recipient_name || "-"}</span>
                            </div>
                            <div className="flex flex-col gap-1">
                              <span className="text-zinc-500 text-[11px] uppercase tracking-wider font-semibold">Company</span>
                              <span className="text-zinc-200 font-medium">{track.company || "-"}</span>
                            </div>
                            <div className="flex flex-col gap-1">
                              <span className="text-zinc-500 text-[11px] uppercase tracking-wider font-semibold">Email</span>
                              <span className="text-zinc-200 font-medium truncate" title={track.email}>{track.email}</span>
                            </div>
                          </div>
                        </div>

                        {/* Engagement Timeline */}
                        <div>
                          <h3 className="text-zinc-300 font-semibold text-sm border-b border-zinc-800/60 pb-3 mb-3">Engagement</h3>
                          <div className="flex flex-col gap-4 text-sm max-h-[160px] overflow-y-auto custom-scrollbar pr-2">
                            {track.open_count > 0 ? (
                              <div className="flex items-start gap-3">
                                <CheckCircle2 size={16} className="text-emerald-400 mt-0.5 shrink-0" />
                                <div className="flex flex-col">
                                  <span className="text-zinc-200 font-medium">Opened Email ({track.open_count}x)</span>
                                  <span className="text-zinc-500 text-[11px] mt-0.5">
                                    Last opened: {new Date(track.opened_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                                  </span>
                                </div>
                              </div>
                            ) : (
                              <div className="flex items-start gap-3">
                                <AlertCircle size={16} className="text-zinc-600 mt-0.5 shrink-0" />
                                <span className="text-zinc-500">Not opened yet</span>
                              </div>
                            )}

                            {track.clicks && track.clicks.map((click: any, idx: number) => {
                              try {
                                const urlObj = new URL(click.url);
                                return (
                                  <div key={idx} className="flex items-start gap-3 relative before:absolute before:left-[-11px] before:-top-3 before:h-4 before:w-px before:bg-zinc-800/60 ml-2.5">
                                    <Link2 size={14} className="text-blue-400 mt-1 shrink-0 relative z-10 bg-zinc-950" />
                                    <div className="flex flex-col overflow-hidden w-full">
                                      <span className="text-zinc-200 font-medium">Clicked Link</span>
                                      <a href={click.url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline text-xs truncate max-w-full" title={click.url}>
                                        {urlObj.hostname.replace('www.', '')}{urlObj.pathname !== '/' ? '...' : ''}
                                      </a>
                                      <span className="text-zinc-500 text-[11px] mt-0.5">
                                        {new Date(click.clicked_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                                      </span>
                                    </div>
                                  </div>
                                );
                              } catch {
                                return null;
                              }
                            })}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
