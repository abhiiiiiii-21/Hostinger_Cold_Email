"use client";

import React, { useState, useEffect } from "react";
import { Send, Users, CheckCircle2, AlertCircle, RefreshCw, Paperclip, X, Trash2 } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import dynamic from "next/dynamic";
import "react-quill-new/dist/quill.snow.css";

const ReactQuill = dynamic(() => import("react-quill-new"), { ssr: false });

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export default function InboxPage() {
  const { getToken } = useAuth();
  
  // Composer State
  const [email, setEmail] = useState("");
  const [cc, setCc] = useState("");
  const [bcc, setBcc] = useState("");
  const [showCcBcc, setShowCcBcc] = useState(false);
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [attachments, setAttachments] = useState<File[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [sendStatus, setSendStatus] = useState<{type: "success" | "error" | null, message: string}>({type: null, message: ""});

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
    return () => clearInterval(interval);
  }, []);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !name || !subject || !body) return;
    
    // Check total attachment size (25MB)
    const totalSize = attachments.reduce((acc, file) => acc + file.size, 0);
    if (totalSize > 25 * 1024 * 1024) {
      setSendStatus({type: "error", message: "Total attachments size exceeds 25MB limit."});
      return;
    }
    
    setIsSending(true);
    setSendStatus({type: null, message: ""});
    
    try {
      const formData = new FormData();
      formData.append("email", email);
      formData.append("cc", cc);
      formData.append("bcc", bcc);
      formData.append("name", name);
      formData.append("company", company);
      formData.append("subject", subject);
      formData.append("body", body);
      
      attachments.forEach(file => {
        formData.append("attachments", file);
      });

      const res = await fetch(`${API_BASE}/single-send`, {
        method: "POST",
        headers: {
          "x-api-key": "websual_dev_secret_key",
          "x-user-id": "dev_user_123"
        },
        body: formData
      });
      
      const data = await res.json();
      
      if (res.ok && data.status === "success") {
        setSendStatus({type: "success", message: "Email sent successfully with tracking!"});
        // Clear form
        setEmail("");
        setCc("");
        setBcc("");
        setName("");
        setCompany("");
        setSubject("");
        setBody("");
        setAttachments([]);
        // Refresh tracking data
        fetchTracking();
      } else {
        setSendStatus({type: "error", message: data.message || "Failed to send email."});
      }
    } catch (err: any) {
      setSendStatus({type: "error", message: err.message || "An error occurred."});
    }
    setIsSending(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] space-y-4 pb-4">
      <div className="shrink-0">
        <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">Inbox</h1>
        <p className="text-zinc-500 text-sm mt-1">Send and track personalized, one-off emails.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
        
        {/* COMPOSER FORM */}
        <div className="bg-zinc-950/50 border border-zinc-800/60 rounded-2xl overflow-hidden flex flex-col h-full">
          <div className="p-5 border-b border-zinc-800/60 bg-zinc-900/40 shrink-0">
            <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Send size={16} className="text-zinc-400" />
              Compose Email
            </h2>
          </div>
          
          <div className="p-6 flex-1 overflow-y-auto custom-scrollbar">
            <form onSubmit={handleSend} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5 relative">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-medium text-zinc-400">Recipient Email *</label>
                    {!showCcBcc && (
                      <button 
                        type="button" 
                        onClick={() => setShowCcBcc(true)}
                        className="text-[10px] text-zinc-500 hover:text-zinc-300 font-medium"
                      >
                        Cc / Bcc
                      </button>
                    )}
                  </div>
                  <input 
                    type="email" 
                    required 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700" 
                    placeholder="client@example.com"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-zinc-400">Full Name *</label>
                  <input 
                    type="text" 
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700" 
                    placeholder="John Doe"
                  />
                </div>
              </div>
              
              {showCcBcc && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-zinc-400">Cc</label>
                    <input 
                      type="text" 
                      value={cc}
                      onChange={(e) => setCc(e.target.value)}
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700" 
                      placeholder="manager@example.com"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-zinc-400">Bcc</label>
                    <input 
                      type="text" 
                      value={bcc}
                      onChange={(e) => setBcc(e.target.value)}
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700" 
                      placeholder="hidden@example.com"
                    />
                  </div>
                </div>
              )}
              
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-400">Company Name</label>
                <input 
                  type="text" 
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700" 
                  placeholder="Acme Corp"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-400">Subject *</label>
                <input 
                  type="text" 
                  required
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700" 
                  placeholder="Quick question about your website"
                />
              </div>

              <div className="space-y-1.5 flex-1 flex flex-col pb-4 min-h-0">
                <label className="text-xs font-medium text-zinc-400 shrink-0">Message *</label>
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden text-zinc-200 flex-1 flex flex-col min-h-[150px]">
                  <ReactQuill 
                    theme="snow"
                    value={body}
                    onChange={setBody}
                    className="flex-1 flex flex-col h-full custom-quill"
                  />
                </div>
              </div>

              <div className="space-y-2 mt-4 pt-4 border-t border-zinc-800/50 shrink-0">
                <label className="text-xs font-medium text-zinc-400 flex items-center gap-1.5">
                  <Paperclip size={14} />
                  Attachments (Max 25MB total)
                </label>
                <input 
                  type="file" 
                  multiple 
                  onChange={(e) => {
                    if (e.target.files) {
                      setAttachments(Array.from(e.target.files));
                    }
                  }}
                  className="w-full text-xs text-zinc-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-zinc-800 file:text-zinc-300 hover:file:bg-zinc-700 transition"
                />
                
                {attachments.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {attachments.map((file, idx) => (
                      <div key={idx} className="flex items-center gap-2 bg-zinc-800/50 px-2 py-1 rounded text-xs text-zinc-300 border border-zinc-700/50">
                        <span className="truncate max-w-[150px]">{file.name}</span>
                        <span className="text-[10px] text-zinc-500">{(file.size / 1024 / 1024).toFixed(1)}MB</span>
                        <button 
                          type="button" 
                          onClick={() => setAttachments(attachments.filter((_, i) => i !== idx))}
                          className="text-zinc-500 hover:text-red-400"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {sendStatus.type && (
                <div className={`p-3 rounded-lg text-sm border ${sendStatus.type === 'success' ? 'bg-emerald-950/30 border-emerald-900/50 text-emerald-400' : 'bg-red-950/30 border-red-900/50 text-red-400'}`}>
                  {sendStatus.message}
                </div>
              )}
            </form>
          </div>
          
          <div className="p-5 border-t border-zinc-800/60 bg-zinc-900/20 shrink-0 flex justify-end">
            <button 
              onClick={handleSend}
              disabled={isSending || !email || !name || !subject || !body}
              className="px-6 py-2 bg-zinc-100 hover:bg-white text-zinc-950 text-sm font-semibold rounded-lg transition disabled:opacity-50 flex items-center gap-2"
            >
              {isSending ? (
                <><RefreshCw size={14} className="animate-spin" /> Sending...</>
              ) : (
                <><Send size={14} /> Send Email</>
              )}
            </button>
          </div>
        </div>

        {/* TRACKING TABLE */}
        <div className="bg-zinc-950/50 border border-zinc-800/60 rounded-2xl overflow-hidden flex flex-col h-full">
          <div className="p-5 border-b border-zinc-800/60 bg-zinc-900/40 shrink-0 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Users size={16} className="text-zinc-400" />
              Sent Items & Tracking
            </h2>
            <button 
              onClick={fetchTracking}
              disabled={isLoading}
              className="text-zinc-500 hover:text-zinc-300 transition"
              title="Refresh Tracking Data"
            >
              <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto custom-scrollbar p-0">
            {trackingData.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-zinc-500 space-y-3">
                <Send size={32} className="opacity-20" />
                <p className="text-sm font-medium">No personalized emails sent yet.</p>
              </div>
            ) : (
              <table className="w-full text-left text-sm text-zinc-400">
                <thead className="bg-zinc-900/60 text-xs uppercase text-zinc-500 font-semibold sticky top-0 backdrop-blur-md z-10">
                  <tr>
                    <th className="px-4 py-3">Recipient</th>
                    <th className="px-4 py-3">Subject & Message</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Clicks</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/50">
                  {trackingData.map(track => (
                    <tr key={track.tracking_id} className="hover:bg-zinc-900/40">
                      <td className="px-4 py-3 max-w-[200px]">
                        {track.recipient_name && <p className="text-zinc-100 font-semibold mb-0.5 truncate">{track.recipient_name}</p>}
                        <p className="text-xs text-zinc-500 truncate">{track.email}</p>
                        <p className="text-[10px] text-zinc-600 mt-1">
                          Sent: {new Date(track.sent_at).toLocaleDateString()}
                        </p>
                      </td>
                      <td className="px-4 py-3 max-w-[250px] align-top">
                        <p className="text-xs text-zinc-300 font-medium truncate mb-1" title={track.email_subject || "No Subject"}>
                          {track.email_subject || "No Subject"}
                        </p>
                        {track.email_body ? (
                          <div className="flex flex-col items-start gap-2 mt-1">
                            <button 
                              onClick={() => setExpandedBodyId(expandedBodyId === track.tracking_id ? null : track.tracking_id)}
                              className="text-[10px] text-blue-400 hover:text-blue-300 hover:underline transition"
                            >
                              {expandedBodyId === track.tracking_id ? "Hide Message" : "View Message"}
                            </button>
                            {expandedBodyId === track.tracking_id && (
                              <div className="w-full bg-zinc-950 border border-zinc-800/80 rounded-md p-3 text-xs text-zinc-400 max-h-[150px] overflow-y-auto custom-scrollbar shadow-inner mt-1">
                                <div dangerouslySetInnerHTML={{ __html: track.email_body }} />
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-[10px] text-zinc-600">No message stored</span>
                        )}
                      </td>
                      <td className="px-4 py-3 align-top">
                        {track.open_count > 0 ? (
                          <div className="flex flex-col gap-1">
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 w-fit rounded bg-emerald-950/50 text-emerald-400 text-[11px] font-medium border border-emerald-900/50">
                              <CheckCircle2 size={10} strokeWidth={1.75} /> Opened ({track.open_count})
                            </span>
                            <span className="text-[10px] text-zinc-500">
                              {new Date(track.opened_at).toLocaleDateString()} {new Date(track.opened_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </span>
                            {track.city && (
                              <span className="text-[10px] text-zinc-400 font-medium mt-0.5">
                                📍 {track.city}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-zinc-900 text-zinc-500 text-[11px] font-medium border border-zinc-800">
                            <AlertCircle size={10} strokeWidth={1.75} /> Unopened
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs max-w-[200px] align-top">
                        {track.clicks && track.clicks.length > 0 ? (
                          <div className="flex flex-col gap-1.5">
                            {track.clicks.map((click: any, idx: number) => {
                              try {
                                const urlObj = new URL(click.url);
                                return (
                                  <div key={idx} className="flex flex-col">
                                    <a href={click.url} target="_blank" rel="noreferrer" className="text-blue-400 hover:text-blue-300 hover:underline truncate" title={click.url}>
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
                        <div className="mt-2 flex justify-end">
                          <button 
                            onClick={() => handleDelete(track.tracking_id)} 
                            className="p-1 text-zinc-500 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                            title="Delete Record"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
