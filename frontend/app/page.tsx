"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Send, 
  BarChart3, 
  Users, 
  Play,
  Square,
  UploadCloud,
  CheckCircle2,
  XCircle,
  AlertCircle,
  TerminalSquare,
  FastForward,
  ServerCrash,
  Copy
} from "lucide-react";
import { motion } from "framer-motion";

const API_BASE = "http://127.0.0.1:8000/api";

export default function Dashboard() {
  const [selectedCountry, setSelectedCountry] = useState("USA");
  const [file, setFile] = useState<File | null>(null);
  const [forceSend, setForceSend] = useState(false);
  const [batchSize, setBatchSize] = useState<number>(60);
  const [cooldownMinutes, setCooldownMinutes] = useState<number>(20);
  const [previewData, setPreviewData] = useState<{total: number, breakdown: Record<string, number>} | null>(null);
  
  // Stats
  const [stats, setStats] = useState({ today: 0, yesterday: 0, month: 0, today_opens: 0 });

  // System State from Backend
  const [backendStatus, setBackendStatus] = useState<"offline" | "online" | "error">("offline");
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isCoolingDown, setIsCoolingDown] = useState(false);
  const [progress, setProgress] = useState(0);
  const [processed, setProcessed] = useState(0);
  const [totalLeads, setTotalLeads] = useState(0);
  
  // Speed metrics
  const [currentDelay, setCurrentDelay] = useState(0);
  const [averageSendTime, setAverageSendTime] = useState(0);
  const [estimatedCompletion, setEstimatedCompletion] = useState(0);
  
  const [sentList, setSentList] = useState<{company: string, email: string}[]>([]);
  const [failedList, setFailedList] = useState<{company: string, email: string, error: string}[]>([]);
  const [skippedList, setSkippedList] = useState<{company: string, email: string, reason: string}[]>([]);
  const [logs, setLogs] = useState<{time: string, type: string, message: string}[]>([]);
  const [copied, setCopied] = useState(false);

  // History State
  const [history, setHistory] = useState<any[]>([]);
  const [currentView, setCurrentView] = useState<"dashboard" | "history">("dashboard");
  const [expandedCampaign, setExpandedCampaign] = useState<number | null>(null);
  const [campaignTracking, setCampaignTracking] = useState<any[]>([]);
  const isRunningRef = useRef(isRunning);

  useEffect(() => {
    isRunningRef.current = isRunning;
  }, [isRunning]);

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

  // Tabs for the execution monitor
  const [activeTab, setActiveTab] = useState<"logs" | "success" | "failed" | "skipped">("logs");

  // Fetch initial stats
  useEffect(() => {
    fetch(`${API_BASE}/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Failed to fetch stats", err));
  }, []);

  // Poll backend state every 1 second
  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`${API_BASE}/state`)
        .then(res => {
          if (!res.ok) throw new Error("Network response was not ok");
          return res.json();
        })
        .then(data => {
          setBackendStatus(data.failedList.length > 0 ? "error" : "online");
          
          if (isRunningRef.current && !data.isRunning) {
            fetchHistory();
          }

          setIsRunning(data.isRunning);
          setIsPaused(data.isPaused);
          setIsCoolingDown(data.isCoolingDown);
          setProgress(data.progress);
          setProcessed(data.processed);
          setTotalLeads(data.totalLeads);
          setSentList(data.sentList);
          setFailedList(data.failedList);
          setSkippedList(data.skippedList);
          setLogs(data.logs);
          
          setCurrentDelay(data.currentDelay || 0);
          setAverageSendTime(data.averageSendTime || 0);
          setEstimatedCompletion(data.estimatedCompletion || 0);
        })
        .catch(err => {
          setBackendStatus("offline");
          console.error("Failed to fetch state", err);
        });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setPreviewData(null);
      
      try {
        const formData = new FormData();
        formData.append("file", selectedFile);
        const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
        if (res.ok) {
          const data = await res.json();
          setPreviewData({ total: data.total, breakdown: data.breakdown });
        } else {
          const errData = await res.json();
          alert(`Error reading CSV: ${errData.error || 'Unknown error'}`);
          setFile(null);
        }
      } catch (err) {
        console.error("Failed to parse CSV preview", err);
        alert("Failed to parse CSV preview. Check the console for details.");
        setFile(null);
      }
    }
  };

  const handleRunCampaign = async () => {
    if (!file) {
      alert("Please select a CSV file first.");
      return;
    }

    try {
      // Start the campaign
      const startRes = await fetch(`${API_BASE}/start?country=${selectedCountry}&force_send=${forceSend}&batch_size=${batchSize}&cooldown_minutes=${cooldownMinutes}`, { method: "POST" });
      const startData = await startRes.json();
      
      if (startData.status === "error") {
        alert(startData.message);
      } else {
        setActiveTab("logs");
      }
      
    } catch (err) {
      alert("Error starting campaign: " + err);
    }
  };

  const handleStopCampaign = async () => {
    try {
      await fetch(`${API_BASE}/stop`, { method: "POST" });
    } catch (err) {
      alert("Error stopping campaign: " + err);
    }
  };

  const handlePauseCampaign = async () => {
    try {
      await fetch(`${API_BASE}/pause`, { method: "POST" });
    } catch (err) {
      alert("Error pausing campaign: " + err);
    }
  };

  const handleResumeCampaign = async () => {
    try {
      await fetch(`${API_BASE}/resume`, { method: "POST" });
    } catch (err) {
      alert("Error resuming campaign: " + err);
    }
  };

  const formatTime = (seconds: number) => {
    const roundedSeconds = Math.round(seconds);
    if (roundedSeconds < 60) return `${roundedSeconds} sec`;
    const mins = Math.floor(roundedSeconds / 60);
    const secs = roundedSeconds % 60;
    return `${mins} min ${secs > 0 ? secs + ' sec' : ''}`;
  };

  const getLogColor = (type: string) => {
    switch(type) {
      case "INFO": return "text-zinc-500";
      case "PROCESS": return "text-indigo-400";
      case "SEND": return "text-zinc-300";
      case "SUCCESS": return "text-emerald-400";
      case "SKIP": return "text-amber-400/80";
      case "ERROR": return "text-red-400";
      case "SYSTEM": return "text-zinc-600";
      case "WARN": return "text-red-400 font-bold";
      default: return "text-zinc-400";
    }
  };

  const handleCopyLogs = () => {
    const logText = logs.map(l => `[${l.time}] [${l.type}] ${l.message}`).join('\n');
    navigator.clipboard.writeText(logText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-[#0c0c0e] text-zinc-300 flex flex-col font-sans selection:bg-zinc-200 selection:text-zinc-900">
      
      {/* TOP HEADER */}
      <header className="h-16 flex items-center justify-between px-8 bg-zinc-950/30 backdrop-blur-md border-b border-zinc-800/60 sticky top-0 z-10">
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
            <button 
              onClick={() => setCurrentView("dashboard")}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition ${currentView === "dashboard" ? "bg-zinc-900 text-zinc-100 shadow-sm" : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/40"}`}
            >
              <BarChart3 size={18} />
              <span className="font-medium text-sm">Dashboard</span>
            </button>
            <button 
              onClick={() => setCurrentView("history")}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition ${currentView === "history" ? "bg-zinc-900 text-zinc-100 shadow-sm" : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/40"}`}
            >
              <TerminalSquare size={18} />
              <span className="font-medium text-sm">Campaign History</span>
            </button>
          </div>
        </aside>

        {/* DASHBOARD CONTENT */}
        <main className="flex-1 overflow-auto p-8 w-full relative">
          <div className="max-w-[1400px] mx-auto">
            {currentView === "dashboard" ? (
              <>
                {/* STATS ROW */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard title="Sent Today" value={stats.today.toString()} icon={<CheckCircle2 size={20} className="text-zinc-400" />} />
          <StatCard title="Today's Opens" value={`${stats.today_opens} / ${stats.today}`} trend={stats.today > 0 ? `${Math.round((stats.today_opens / stats.today) * 100)}%` : "0%"} icon={<Play size={20} className="text-zinc-400" />} />
          <StatCard title="Sent Yesterday" value={stats.yesterday.toString()} icon={<Users size={20} className="text-zinc-400" />} />
          <StatCard title="Monthly Volume" value={stats.month.toString()} icon={<BarChart3 size={20} className="text-zinc-400" />} />
        </div>

        {/* LAUNCH CAMPAIGN & LOGS */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* LEFT COLUMN: SETUP */}
          <div className="lg:col-span-4 flex flex-col gap-6">
            
            <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-2xl p-6 shadow-sm backdrop-blur-sm relative overflow-hidden">
              <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-zinc-700/50 to-transparent"></div>
              
              <h2 className="text-base font-semibold text-zinc-100 mb-6 tracking-tight">Launch Campaign</h2>
              
              <div className="space-y-6">
                {/* Country Selection */}
                <div>
                  <label className="block text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">Target Country</label>
                  <select 
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3.5 text-zinc-200 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-600 focus:border-zinc-600 transition appearance-none shadow-inner"
                    value={selectedCountry}
                    onChange={(e) => setSelectedCountry(e.target.value)}
                  >
                    <option value="USA">United States</option>
                    <option value="UK">United Kingdom</option>
                    <option value="UAE">United Arab Emirates</option>
                  </select>
                </div>

                {/* CSV Uploader */}
                <div>
                  <label className="block text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">Lead Data</label>
                  <label className="flex flex-col items-center justify-center w-full h-36 bg-zinc-950/50 border border-dashed border-zinc-700 rounded-xl cursor-pointer hover:bg-zinc-900 hover:border-zinc-500 transition group">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6 text-center px-4">
                      <UploadCloud className="w-6 h-6 text-zinc-500 group-hover:text-zinc-300 transition mb-3" />
                      <p className="text-sm text-zinc-300 font-medium truncate max-w-[200px]">
                        {file ? file.name : "Select CSV file"}
                      </p>
                      <p className="text-xs text-zinc-600 mt-1">Template is auto-assigned via Review column</p>
                    </div>
                    <input 
                      type="file" 
                      className="hidden" 
                      accept=".csv"
                      onChange={handleFileChange}
                    />
                  </label>
                </div>

                {/* Queue Preview */}
                {previewData && (
                  <div>
                    <label className="block text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">Queue Preview</label>
                    <div className="bg-zinc-950/50 border border-zinc-800 rounded-xl p-4 font-mono text-sm space-y-4">
                      <p className="text-zinc-200">{previewData.total} Leads</p>
                      {Object.entries(previewData.breakdown).map(([cat, count]) => (
                        <div key={cat} className="flex flex-col">
                          <span className="text-zinc-400">{cat}</span>
                          <span className="text-zinc-200">{count as React.ReactNode}</span>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-zinc-500 mt-2">This lets you verify the CSV before starting.</p>
                  </div>
                )}

                {/* Force Send Checkbox */}
                <div className="flex items-center gap-3 bg-zinc-950/50 border border-zinc-800 p-3.5 rounded-xl transition hover:border-zinc-700">
                  <input 
                    type="checkbox" 
                    id="forceSend"
                    checked={forceSend}
                    onChange={(e) => setForceSend(e.target.checked)}
                    className="w-4 h-4 rounded bg-zinc-900 border-zinc-700 text-zinc-100 focus:ring-zinc-600 focus:ring-offset-zinc-950 cursor-pointer"
                  />
                  <label htmlFor="forceSend" className="text-xs text-zinc-400 font-medium cursor-pointer flex-1 select-none">
                    Bypass duplicate check (Send to previously emailed leads)
                  </label>
                </div>

                {/* Batch Limit & Cooldown Configuration */}
                <div className="bg-zinc-950/50 border border-zinc-800 p-4 rounded-xl space-y-4">
                  <div className="flex justify-between items-center mb-1">
                    <label className="block text-xs font-medium text-zinc-400 uppercase tracking-wider">Spam Prevention</label>
                    <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Anti-Spam</span>
                  </div>
                  
                  <div className="flex gap-4">
                    <div className="flex-1">
                      <label className="block text-[11px] font-medium text-zinc-500 mb-1.5">Batch Size</label>
                      <input 
                        type="number"
                        min="0"
                        value={batchSize}
                        onChange={(e) => setBatchSize(Number(e.target.value))}
                        className="w-full bg-zinc-900 border border-zinc-700/50 rounded-lg px-3 py-2 text-zinc-200 text-sm focus:outline-none focus:border-zinc-500 transition shadow-inner"
                        placeholder="e.g. 60"
                      />
                      <p className="text-[10px] text-zinc-500 mt-1.5">Emails before pausing</p>
                    </div>
                    
                    <div className="flex-1">
                      <label className="block text-[11px] font-medium text-zinc-500 mb-1.5">Cooldown Wait</label>
                      <div className="relative">
                        <input 
                          type="number"
                          min="0"
                          value={cooldownMinutes}
                          onChange={(e) => setCooldownMinutes(Number(e.target.value))}
                          className="w-full bg-zinc-900 border border-zinc-700/50 rounded-lg px-3 py-2 text-zinc-200 text-sm focus:outline-none focus:border-zinc-500 transition shadow-inner"
                          placeholder="e.g. 20"
                        />
                        <span className="absolute right-3 top-2 text-xs font-medium text-zinc-500">min</span>
                      </div>
                      <p className="text-[10px] text-zinc-500 mt-1.5">Time to pause sending</p>
                    </div>
                  </div>
                  <p className="text-[11px] text-zinc-500 italic border-t border-zinc-800/50 pt-2">
                    Tip: Send in batches and wait (e.g. 60 emails, wait 20 min) to protect your domain reputation.
                  </p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            {!isRunning ? (
              <button 
                onClick={handleRunCampaign}
                disabled={!file || backendStatus === "offline"}
                className={`w-full py-4 px-4 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-all duration-300 ${
                  !file || backendStatus === "offline"
                    ? "bg-zinc-900 text-zinc-600 border border-zinc-800 cursor-not-allowed" 
                    : "bg-zinc-100 hover:bg-white text-zinc-900 shadow-[0_0_20px_rgba(255,255,255,0.05)] hover:shadow-[0_0_25px_rgba(255,255,255,0.1)] active:scale-[0.98]"
                }`}
              >
                <Play size={16} fill={!file || backendStatus === "offline" ? "transparent" : "currentColor"} />
                Execute Campaign
              </button>
            ) : (
              <div className="flex gap-4">
                {!isPaused ? (
                  <button 
                    onClick={handlePauseCampaign}
                    className="flex-1 py-4 px-4 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-all duration-300 bg-amber-950/40 text-amber-400 border border-amber-900/50 hover:bg-amber-900/40 hover:text-amber-300 shadow-[0_0_20px_rgba(251,191,36,0.1)] active:scale-[0.98]"
                  >
                    <Square size={14} fill="currentColor" />
                    Pause
                  </button>
                ) : (
                  <button 
                    onClick={handleResumeCampaign}
                    className="flex-1 py-4 px-4 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-all duration-300 bg-emerald-950/40 text-emerald-400 border border-emerald-900/50 hover:bg-emerald-900/40 hover:text-emerald-300 shadow-[0_0_20px_rgba(52,211,153,0.1)] active:scale-[0.98]"
                  >
                    <Play size={14} fill="currentColor" />
                    Resume
                  </button>
                )}
                
                <button 
                  onClick={handleStopCampaign}
                  className="flex-1 py-4 px-4 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-all duration-300 bg-red-950/40 text-red-400 border border-red-900/50 hover:bg-red-900/40 hover:text-red-300 shadow-[0_0_20px_rgba(220,38,38,0.1)] active:scale-[0.98]"
                >
                  <Square size={14} fill="currentColor" />
                  Stop
                </button>
              </div>
            )}
          </div>

          {/* RIGHT COLUMN: TERMINAL & TRACKER */}
          <div className="lg:col-span-8 flex flex-col gap-6 h-[600px]">
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 shrink-0">
              {/* Progress Bar Module */}
              <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-2xl p-6 shadow-sm backdrop-blur-sm relative overflow-hidden flex flex-col justify-center">
                <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-zinc-700/50 to-transparent"></div>
                
                <div className="flex justify-between items-end mb-4">
                  <div>
                    <h2 className="text-base font-semibold text-zinc-100 tracking-tight">Transmission Status</h2>
                    <p className="text-xs text-zinc-500 mt-1">Live progress of outgoing emails</p>
                  </div>
                  <span className="text-2xl font-light text-zinc-200">{progress}%</span>
                </div>
                
                <div className="w-full h-1.5 bg-zinc-950 rounded-full overflow-hidden border border-zinc-800/50 shadow-inner mt-auto">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    className={`h-full ${backendStatus === "error" ? "bg-gradient-to-r from-red-600 to-red-400" : "bg-gradient-to-r from-zinc-600 to-zinc-300"}`}
                  />
                </div>
                
                <div className="flex justify-between mt-4 text-xs font-medium text-zinc-500">
                  <div className="flex gap-4">
                    <span>Total: {totalLeads}</span>
                    <span className="text-zinc-700">|</span>
                    <span>{processed} Processed</span>
                  </div>
                  <div className="flex gap-4">
                    <span className="flex items-center gap-1.5"><CheckCircle2 size={12} className="text-zinc-400"/> {sentList.length} Sent</span>
                    <span className="flex items-center gap-1.5"><FastForward size={12} className="text-zinc-500"/> {skippedList.length} Skip</span>
                  </div>
                </div>
              </div>

              {/* Live Speed Module */}
              <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-2xl p-6 shadow-sm backdrop-blur-sm relative overflow-hidden flex flex-col justify-center">
                <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-zinc-700/50 to-transparent"></div>
                <h2 className="text-base font-semibold text-zinc-100 tracking-tight mb-4">Live Speed</h2>
                <div className="space-y-3 font-mono text-sm">
                  <div className="flex justify-between items-center">
                    <span className={isCoolingDown ? "text-amber-500 font-semibold" : "text-zinc-500"}>
                      {isCoolingDown ? "Cooldown Timer" : "Current Delay"}
                    </span>
                    <span className={isCoolingDown ? "text-amber-400" : "text-zinc-200"}>
                      {!isRunning ? '-' : currentDelay > 0 ? formatTime(currentDelay) : 'Wait...'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-500">Average Send Time</span>
                    <span className="text-zinc-200">{!isRunning ? '-' : averageSendTime > 0 ? `${averageSendTime} sec` : 'Wait...'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-500">Estimated Completion</span>
                    <span className="text-zinc-200">{!isRunning ? '-' : estimatedCompletion > 0 ? formatTime(estimatedCompletion) : 'Wait...'}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Live Execution Monitor (Tabs) */}
            <div className="flex-1 bg-zinc-950 border border-zinc-800/80 rounded-2xl font-mono text-[13px] overflow-hidden flex flex-col relative shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)]">
              
              {/* Tabs Header */}
              <div className="flex justify-between items-center border-b border-zinc-800/80 bg-zinc-900/30 overflow-x-auto pr-3">
                <div className="flex items-center">
                  <button 
                    onClick={() => setActiveTab("logs")}
                    className={`flex items-center gap-2 px-5 py-3 transition whitespace-nowrap ${activeTab === "logs" ? "text-zinc-100 border-b border-zinc-300 bg-zinc-900/50" : "text-zinc-500 hover:text-zinc-300"}`}
                  >
                    <TerminalSquare size={14} /> Live Logs
                  </button>
                <button 
                  onClick={() => setActiveTab("success")}
                  className={`flex items-center gap-2 px-5 py-3 transition whitespace-nowrap ${activeTab === "success" ? "text-zinc-100 border-b border-zinc-300 bg-zinc-900/50" : "text-zinc-500 hover:text-zinc-300"}`}
                >
                  <CheckCircle2 size={14} /> Sent ({sentList.length})
                </button>
                <button 
                  onClick={() => setActiveTab("skipped")}
                  className={`flex items-center gap-2 px-5 py-3 transition whitespace-nowrap ${activeTab === "skipped" ? "text-zinc-100 border-b border-zinc-300 bg-zinc-900/50" : "text-zinc-500 hover:text-zinc-300"}`}
                >
                  <FastForward size={14} /> Skipped ({skippedList.length})
                </button>
                <button 
                  onClick={() => setActiveTab("failed")}
                  className={`flex items-center gap-2 px-5 py-3 transition whitespace-nowrap ${activeTab === "failed" ? "text-zinc-100 border-b border-zinc-300 bg-zinc-900/50" : "text-zinc-500 hover:text-zinc-300"}`}
                >
                  <XCircle size={14} /> Failed ({failedList.length})
                </button>
                </div>
                
                {activeTab === "logs" && logs.length > 0 && (
                  <button 
                    onClick={handleCopyLogs}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-zinc-800/50 hover:bg-zinc-700/50 text-zinc-300 text-xs transition"
                    title="Copy logs to clipboard"
                  >
                    {copied ? <CheckCircle2 size={14} className="text-emerald-400" /> : <Copy size={14} />}
                    {copied ? "Copied" : "Copy Logs"}
                  </button>
                )}
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-y-auto p-5 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent flex flex-col">
                
                {/* LOGS TAB */}
                {activeTab === "logs" && (
                  <div className="space-y-1.5 flex-1">
                    {logs.length === 0 && !isRunning ? (
                      <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-3">
                        <AlertCircle size={20} className="opacity-40" />
                        <p>System idle. Awaiting execution command.</p>
                      </div>
                    ) : (
                      logs.map((log, idx) => (
                        <div key={idx} className="flex gap-3 hover:bg-zinc-900/50 px-2 py-1 rounded transition-colors">
                          <span className="text-zinc-600 shrink-0">[{log.time}]</span>
                          <span className={`w-16 shrink-0 font-semibold ${getLogColor(log.type)}`}>[{log.type}]</span>
                          <span className="text-zinc-300">{log.message}</span>
                        </div>
                      ))
                    )}
                    {/* Auto scroll anchor hack */}
                    <div style={{ float:"left", clear: "both" }}></div>
                  </div>
                )}

                {/* SUCCESS TAB */}
                {activeTab === "success" && (
                  <div className="space-y-2">
                    {sentList.length === 0 ? (
                      <p className="text-zinc-600 text-center pt-20">No emails sent yet.</p>
                    ) : (
                      sentList.map((item, idx) => (
                        <div key={idx} className="flex justify-between items-center p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
                          <div>
                            <p className="text-zinc-200 font-medium">{item.company}</p>
                            <p className="text-zinc-500">{item.email}</p>
                          </div>
                          <span className="text-zinc-400 flex items-center gap-1.5"><CheckCircle2 size={14}/> Sent</span>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* SKIPPED TAB */}
                {activeTab === "skipped" && (
                  <div className="space-y-2">
                    {skippedList.length === 0 ? (
                      <p className="text-zinc-600 text-center pt-20">No leads skipped yet.</p>
                    ) : (
                      skippedList.map((item, idx) => (
                        <div key={idx} className="flex justify-between items-center p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
                          <div>
                            <p className="text-zinc-200 font-medium">{item.company}</p>
                            <p className="text-zinc-500">{item.email}</p>
                          </div>
                          <span className="text-zinc-500 flex items-center gap-1.5 border border-zinc-800 px-2 py-1 rounded bg-zinc-950 text-xs">
                            <FastForward size={12}/> {item.reason}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* FAILED TAB */}
                {activeTab === "failed" && (
                  <div className="space-y-2">
                    {failedList.length === 0 ? (
                      <p className="text-zinc-600 text-center pt-20">No failures reported.</p>
                    ) : (
                      failedList.map((item, idx) => (
                        <div key={idx} className="flex flex-col p-3 bg-red-950/20 rounded-lg border border-red-900/30">
                          <div className="flex justify-between items-center mb-1">
                            <p className="text-zinc-200 font-medium">{item.company}</p>
                            <span className="text-red-400/80 flex items-center gap-1.5"><XCircle size={14}/> Failed</span>
                          </div>
                          <p className="text-zinc-500">{item.email}</p>
                          <p className="text-red-400/70 mt-2 p-2 bg-red-950/40 rounded border border-red-900/50 text-xs font-medium">Error: {item.error}</p>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </>
    ) : (
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold text-zinc-100 tracking-tight">Campaign History</h2>
                  <p className="text-zinc-500 text-sm mt-1">Review your past email automation runs.</p>
                </div>
                
                <div className="bg-zinc-950/50 border border-zinc-800/60 rounded-2xl overflow-hidden">
                  <table className="w-full text-left text-sm text-zinc-400">
                    <thead className="bg-zinc-900/40 border-b border-zinc-800/60 text-xs uppercase text-zinc-500 font-semibold tracking-wider">
                      <tr>
                        <th className="px-6 py-4">ID</th>
                        <th className="px-6 py-4">Date</th>
                        <th className="px-6 py-4">Country</th>
                        <th className="px-6 py-4">Total</th>
                        <th className="px-6 py-4 text-emerald-500">Sent</th>
                        <th className="px-6 py-4 text-blue-400">Opens</th>
                        <th className="px-6 py-4 text-amber-500">Skipped</th>
                        <th className="px-6 py-4 text-red-500">Failed</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800/50">
                      {history.map(run => (
                        <React.Fragment key={run.id}>
                          <tr 
                            className="hover:bg-zinc-900/40 transition cursor-pointer"
                            onClick={() => handleRowClick(run.id)}
                          >
                            <td className="px-6 py-4 font-mono">#{run.id}</td>
                            <td className="px-6 py-4">
                              {new Date(run.timestamp).toLocaleDateString()} <span className="text-zinc-600">at</span> {new Date(run.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </td>
                            <td className="px-6 py-4 font-medium text-zinc-200">{run.country}</td>
                            <td className="px-6 py-4 font-mono text-zinc-500">{run.total_leads}</td>
                            <td className="px-6 py-4 font-mono text-emerald-400">{run.sent}</td>
                            <td className="px-6 py-4 font-mono text-blue-400">{run.opens || 0}</td>
                            <td className="px-6 py-4 font-mono text-amber-400">{run.skipped}</td>
                            <td className="px-6 py-4 font-mono text-red-400">{run.failed}</td>
                          </tr>
                          
                          {/* Expanded Tracking Details */}
                          {expandedCampaign === run.id && (
                            <tr className="bg-zinc-950/80 border-t-0 shadow-inner">
                              <td colSpan={8} className="p-0">
                                <div className="p-6 border-b border-zinc-800/60 bg-black/20">
                                  <div className="flex items-center justify-between mb-4">
                                    <h4 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
                                      <Users size={16} className="text-zinc-400" />
                                      Recipient Tracking Details (Campaign #{run.id})
                                    </h4>
                                    <span className="text-xs font-medium text-zinc-500">{campaignTracking.length} Sent Emails</span>
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
                                          </tr>
                                        </thead>
                                        <tbody className="divide-y divide-zinc-800/50">
                                          {campaignTracking.map(track => (
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
                                                    <CheckCircle2 size={12} /> Opened
                                                  </span>
                                                ) : (
                                                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-900 text-zinc-500 text-xs font-medium border border-zinc-800">
                                                    <AlertCircle size={12} /> Unopened
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
                                            </tr>
                                          ))}
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
                          <td colSpan={7} className="px-6 py-12 text-center text-zinc-500">No campaigns run yet.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

// Reusable Components
function StatCard({ title, value, icon, trend }: { title: string, value: string, icon: React.ReactNode, trend?: string }) {
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