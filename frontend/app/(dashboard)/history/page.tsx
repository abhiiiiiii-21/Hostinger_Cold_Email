"use client";

import React, { useState, useEffect } from "react";
import { Users, CheckCircle2, AlertCircle, ChevronLeft, ChevronRight, Trash2, Download } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export default function HistoryPage() {
  const [history, setHistory] = useState<any[]>([]);
  const [expandedCampaign, setExpandedCampaign] = useState<number | null>(null);
  const [campaignTracking, setCampaignTracking] = useState<any[]>([]);
  const [trackingFilter, setTrackingFilter] = useState<"all" | "opened" | "unopened">("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [deleteModalOpen, setDeleteModalOpen] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const ITEMS_PER_PAGE = 10;

  const filteredTracking = campaignTracking.filter(track => {
    if (trackingFilter === "opened") return track.open_count > 0;
    if (trackingFilter === "unopened") return track.open_count === 0;
    return true;
  });

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/history`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (err) {}
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleRowClick = async (campaignId: number) => {
    if (expandedCampaign === campaignId) {
      setExpandedCampaign(null);
      return;
    }
    
    setExpandedCampaign(campaignId);
    setTrackingFilter("all");
    try {
      const res = await fetch(`${API_BASE}/history/${campaignId}/tracking`);
      if (res.ok) {
        const data = await res.json();
        setCampaignTracking(data);
      } else {
        setCampaignTracking([]);
      }
    } catch (err) {
      setCampaignTracking([]);
    }
  };

  const confirmDelete = async () => {
    if (deleteModalOpen === null) return;
    setIsDeleting(true);

    try {
      const res = await fetch(`${API_BASE}/history/${deleteModalOpen}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setHistory(prev => prev.filter(c => c.id !== deleteModalOpen));
        if (expandedCampaign === deleteModalOpen) {
          setExpandedCampaign(null);
        }
        setDeleteModalOpen(null);
      } else {
        alert("Failed to delete campaign.");
      }
    } catch (err) {
      alert("Error deleting campaign.");
    }
    setIsDeleting(false);
  };

  const handleDownloadCSV = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (filteredTracking.length === 0) return;

    const headers = [
      "First Name",
      "Last Name",
      "Company Name",
      "Client Email",
      "Website Review",
      "Total Clicks",
      "Clicked URLs",
      "Status"
    ];

    const escapeCsv = (str: string) => `"${(str || "").replace(/"/g, '""')}"`;

    const csvRows = [headers.join(",")];

    filteredTracking.forEach(track => {
      let clickedUrls = "";
      if (track.clicks && track.clicks.length > 0) {
        clickedUrls = track.clicks.map((c: any) => `${c.url} (${new Date(c.clicked_at).toLocaleString()})`).join(" | ");
      }

      const fullName = track.recipient_name || "";
      const nameParts = fullName.split(" ");
      const firstName = nameParts[0] || "";
      const lastName = nameParts.slice(1).join(" ") || "";

      const row = [
        escapeCsv(firstName),
        escapeCsv(lastName),
        escapeCsv(track.company),
        escapeCsv(track.email),
        escapeCsv(track.website_review),
        track.click_count || 0,
        escapeCsv(clickedUrls),
        escapeCsv(track.open_count > 0 ? "Opened" : "Unopened")
      ];
      
      csvRows.push(row.join(","));
    });

    const csvString = csvRows.join("\n");
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `campaign_${expandedCampaign}_tracking_${trackingFilter}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">Campaign History</h1>
        <p className="text-zinc-500 text-sm mt-1">Review your past email automation runs.</p>
      </div>
      
      <div className="bg-zinc-950/50 border border-zinc-800/60 rounded-2xl overflow-hidden">
        <table className="w-full text-left text-sm text-zinc-400">
          <thead className="bg-zinc-900/40 border-b border-zinc-800/60 text-xs uppercase text-zinc-500 font-semibold tracking-wider">
            <tr>
              <th className="px-6 py-4">ID</th>
              <th className="px-6 py-4">Date</th>
              <th className="px-6 py-4">Target</th>
              <th className="px-6 py-4">Total</th>
              <th className="px-6 py-4 text-emerald-500">Sent</th>
              <th className="px-6 py-4 text-blue-400">Opens</th>
              <th className="px-6 py-4 text-amber-500">Skipped</th>
              <th className="px-6 py-4 text-red-500">Failed</th>
              <th className="px-6 py-4"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50">
            {history.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE).map((run, index) => (
              <React.Fragment key={run.id}>
                <tr 
                  className="hover:bg-zinc-900/40 transition cursor-pointer"
                  onClick={() => handleRowClick(run.id)}
                >
                  <td className="px-6 py-4 font-mono">#{ (currentPage - 1) * ITEMS_PER_PAGE + index + 1 }</td>
                  <td className="px-6 py-4">
                    {new Date(run.timestamp).toLocaleDateString()} <span className="text-zinc-600">at</span> {new Date(run.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </td>
                  <td className="px-6 py-4 font-medium text-zinc-200">
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-2">
                        {run.country}
                        <span className="text-[10px] text-zinc-500 bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800 uppercase tracking-wider">
                          {run.email_target === 'email' ? 'Primary' : 'Secondary'}
                        </span>
                      </div>
                      {run.city && run.city !== "NA" && (
                        <span className="text-[11px] text-zinc-400 font-medium">📍 {run.city}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 font-mono text-zinc-500">{run.total_leads}</td>
                  <td className="px-6 py-4 font-mono text-emerald-400">{run.sent}</td>
                  <td className="px-6 py-4 font-mono text-blue-400">{run.opens || 0}</td>
                  <td className="px-6 py-4 font-mono text-amber-400">{run.skipped}</td>
                  <td className="px-6 py-4 font-mono text-red-400">{run.failed}</td>
                  <td className="px-6 py-4 text-right">
                    <button 
                      onClick={(e) => { e.stopPropagation(); setDeleteModalOpen(run.id); }}
                      className="cursor-pointer text-zinc-500 hover:text-red-400 transition p-1.5 rounded hover:bg-red-950/30"
                      title="Delete Campaign"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
                
                {/* Expanded Tracking Details */}
                {expandedCampaign === run.id && (
                  <tr className="bg-zinc-950/80 border-t-0 shadow-inner">
                    <td colSpan={9} className="p-0">
                      <div className="p-6 border-b border-zinc-800/60 bg-black/20">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
                            <Users size={16} strokeWidth={1.75} className="text-zinc-400" />
                            Recipient Tracking Details (Campaign #{run.id})
                          </h4>
                          <div className="flex items-center gap-3">
                            <div className="flex items-center bg-zinc-900/50 rounded-lg p-0.5 border border-zinc-800/80">
                              <button onClick={(e) => { e.stopPropagation(); setTrackingFilter("all"); }} className={`cursor-pointer px-2.5 py-1 text-xs font-medium rounded-md transition ${trackingFilter === "all" ? "bg-zinc-800 text-zinc-200" : "text-zinc-500 hover:text-zinc-300"}`}>All</button>
                              <button onClick={(e) => { e.stopPropagation(); setTrackingFilter("opened"); }} className={`cursor-pointer px-2.5 py-1 text-xs font-medium rounded-md transition ${trackingFilter === "opened" ? "bg-emerald-950/50 text-emerald-400" : "text-zinc-500 hover:text-zinc-300"}`}>Opened</button>
                              <button onClick={(e) => { e.stopPropagation(); setTrackingFilter("unopened"); }} className={`cursor-pointer px-2.5 py-1 text-xs font-medium rounded-md transition ${trackingFilter === "unopened" ? "bg-zinc-800 text-zinc-200" : "text-zinc-500 hover:text-zinc-300"}`}>Unopened</button>
                            </div>
                            <span className="text-xs font-medium text-zinc-500">{filteredTracking.length} / {campaignTracking.length} Sent Emails</span>
                            <button
                              onClick={handleDownloadCSV}
                              disabled={filteredTracking.length === 0}
                              className="cursor-pointer ml-2 p-1.5 bg-zinc-900/50 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 rounded-md border border-zinc-800/80 transition disabled:opacity-50 flex items-center gap-1.5"
                              title="Download CSV"
                            >
                              <Download size={14} />
                              <span className="text-xs font-medium pr-1">CSV</span>
                            </button>
                          </div>
                        </div>
                        
                        {campaignTracking.length === 0 ? (
                          <p className="text-zinc-500 text-sm italic py-4">No tracking data recorded for this campaign.</p>
                        ) : (
                          <div className="max-h-[300px] overflow-y-auto custom-scrollbar border border-zinc-800/80 rounded-xl bg-zinc-900/20">
                            <table className="w-full text-left text-sm text-zinc-400">
                              <thead className="bg-zinc-900/60 text-xs uppercase text-zinc-500 font-semibold sticky top-0 backdrop-blur-md">
                                <tr>
                                  <th className="px-4 py-3">Recipient</th>
                                  <th className="px-4 py-3 w-1/3">Website Review</th>
                                  <th className="px-4 py-3">Status</th>
                                  <th className="px-4 py-3">Last Opened</th>
                                  <th className="px-4 py-3">Total Opens</th>
                                  <th className="px-4 py-3">Clicks</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-zinc-800/50">
                                {filteredTracking.length === 0 ? (
                                  <tr>
                                    <td colSpan={5} className="px-4 py-8 text-center text-zinc-500 italic text-sm">
                                      No results found for this filter.
                                    </td>
                                  </tr>
                                ) : (
                                  filteredTracking.map(track => (
                                    <tr key={track.tracking_id} className="hover:bg-zinc-900/40">
                                      <td className="px-4 py-3">
                                        {track.recipient_name && <p className="text-zinc-100 font-semibold mb-0.5">{track.recipient_name}</p>}
                                        <p className="text-zinc-400 font-medium text-xs mb-0.5">{track.company}</p>
                                        <p className="text-xs text-zinc-500">{track.email}</p>
                                      </td>
                                      <td className="px-4 py-3">
                                        <p className="text-xs text-zinc-400 line-clamp-2" title={track.website_review || "No review provided"}>
                                          {track.website_review || "—"}
                                        </p>
                                      </td>
                                      <td className="px-4 py-3">
                                        {track.open_count > 0 ? (
                                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-950/50 text-emerald-400 text-xs font-medium border border-emerald-900/50">
                                            <CheckCircle2 size={12} strokeWidth={1.75} /> Opened
                                          </span>
                                        ) : (
                                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-900 text-zinc-500 text-xs font-medium border border-zinc-800">
                                            <AlertCircle size={12} strokeWidth={1.75} /> Unopened
                                          </span>
                                        )}
                                      </td>
                                      <td className="px-4 py-3 text-zinc-300 text-xs">
                                        {track.opened_at ? (
                                          <>
                                            {new Date(track.opened_at).toLocaleDateString()} <span className="text-zinc-600">at</span> {new Date(track.opened_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                          </>
                                        ) : (
                                          "-"
                                        )}
                                      </td>
                                      <td className="px-4 py-3 font-mono text-zinc-500">
                                        {track.open_count > 0 ? track.open_count : "-"}
                                      </td>
                                      <td className="px-4 py-3 text-xs">
                                        {track.clicks && track.clicks.length > 0 ? (
                                          <div className="flex flex-col gap-1.5">
                                            {track.clicks.map((click: any, idx: number) => {
                                              try {
                                                const urlObj = new URL(click.url);
                                                return (
                                                  <div key={idx} className="flex flex-col">
                                                    <a href={click.url} target="_blank" rel="noreferrer" className="text-blue-400 hover:text-blue-300 hover:underline truncate max-w-[150px]" title={click.url}>
                                                      {urlObj.hostname.replace('www.', '')}{urlObj.pathname !== '/' ? '...' : ''}
                                                    </a>
                                                    <span className="text-[10px] text-zinc-500">
                                                      {new Date(click.clicked_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                                    </span>
                                                  </div>
                                                );
                                              } catch {
                                                return <span key={idx} className="text-zinc-500">Invalid URL</span>;
                                              }
                                            })}
                                          </div>
                                        ) : (
                                          <span className="text-zinc-600">-</span>
                                        )}
                                      </td>
                                    </tr>
                                  ))
                                )}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
            {history.length === 0 && (
              <tr>
                <td colSpan={9} className="px-6 py-12 text-center text-zinc-500">No campaigns run yet.</td>
              </tr>
            )}
          </tbody>
        </table>

        {history.length > ITEMS_PER_PAGE && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-zinc-800/50 bg-zinc-950">
            <div className="text-sm text-zinc-500 font-medium">
              Showing {((currentPage - 1) * ITEMS_PER_PAGE) + 1} to {Math.min(currentPage * ITEMS_PER_PAGE, history.length)} of {history.length} campaigns
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="cursor-pointer inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 border border-zinc-800 bg-transparent hover:bg-zinc-800 hover:text-zinc-100 h-9 px-4 py-2 text-zinc-300"
              >
                <ChevronLeft className="h-4 w-4 mr-1" strokeWidth={1.75} />
                Previous
              </button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.ceil(history.length / ITEMS_PER_PAGE) }).map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setCurrentPage(i + 1)}
                    className={`cursor-pointer inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none h-9 w-9 ${currentPage === i + 1 ? 'border border-zinc-700 bg-zinc-800 text-zinc-100 shadow-sm' : 'text-zinc-500 hover:bg-zinc-800/50 hover:text-zinc-200'}`}
                  >
                    {i + 1}
                  </button>
                ))}
              </div>
              <button
                onClick={() => setCurrentPage(p => Math.min(Math.ceil(history.length / ITEMS_PER_PAGE), p + 1))}
                disabled={currentPage === Math.ceil(history.length / ITEMS_PER_PAGE)}
                className="cursor-pointer inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 border border-zinc-800 bg-transparent hover:bg-zinc-800 hover:text-zinc-100 h-9 px-4 py-2 text-zinc-300"
              >
                Next
                <ChevronRight className="h-4 w-4 ml-1" strokeWidth={1.75} />
              </button>
            </div>
          </div>
        )}
      </div>

      {deleteModalOpen !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-zinc-950 border border-zinc-800 rounded-xl shadow-2xl p-6 w-full max-w-md animate-in fade-in zoom-in-95 duration-200">
            <h2 className="text-lg font-semibold text-zinc-100">Delete Campaign</h2>
            <p className="text-sm text-zinc-400 mt-2">
              Are you sure you want to completely delete campaign #{deleteModalOpen}? This action cannot be undone and will permanently remove all associated analytics.
            </p>
            <div className="flex justify-end gap-3 mt-6">
              <button 
                onClick={() => setDeleteModalOpen(null)}
                disabled={isDeleting}
                className="cursor-pointer px-4 py-2 rounded-lg text-sm font-medium text-zinc-300 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 transition disabled:opacity-50"
              >
                Cancel
              </button>
              <button 
                onClick={confirmDelete}
                disabled={isDeleting}
                className="cursor-pointer px-4 py-2 rounded-lg text-sm font-medium text-white bg-red-600 hover:bg-red-700 transition disabled:opacity-50 flex items-center gap-2"
              >
                {isDeleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}