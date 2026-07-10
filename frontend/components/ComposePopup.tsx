"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, X, Minus, Maximize2, Minimize2, Paperclip, Trash2, RefreshCw, ChevronDown, CheckCircle2, AlertCircle, Type, Link2 } from "lucide-react";
import dynamic from "next/dynamic";
import "react-quill-new/dist/quill.snow.css";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";
import { toast } from "sonner";
import { useAuth } from "@clerk/nextjs";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
  DropdownMenuGroup,
} from "./ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "./ui/dialog";

const ReactQuill = dynamic(() => import("react-quill-new"), { ssr: false });

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

interface ComposePopupProps {
  onClose: () => void;
  isMinimized: boolean;
  setIsMinimized: (minimized: boolean) => void;
}

export default function ComposePopup({ onClose, isMinimized, setIsMinimized }: ComposePopupProps) {
  const { getToken } = useAuth();
  
  // Composer State
  const [showFormatting, setShowFormatting] = useState(false);
  const quillRef = useRef<any>(null);
  
  // Custom Link State
  const [isLinkDialogOpen, setIsLinkDialogOpen] = useState(false);
  const [linkText, setLinkText] = useState("");
  const [linkUrl, setLinkUrl] = useState("");
  const [linkSelection, setLinkSelection] = useState<any>(null);

  // Custom Schedule State
  const [isCustomScheduleOpen, setIsCustomScheduleOpen] = useState(false);
  const [customScheduleTime, setCustomScheduleTime] = useState("");
  const [showExitConfirm, setShowExitConfirm] = useState(false);

  const handleCloseRequest = () => {
    const hasEmail = email.trim().length > 0;
    const hasSubject = subject.trim().length > 0;
    const bodyText = body.replace(/<[^>]*>?/gm, '').trim();
    const hasBody = bodyText.length > 0;

    if (hasEmail || hasSubject || hasBody) {
      setShowExitConfirm(true);
    } else {
      onClose();
    }
  };

  const [email, setEmail] = useState("");
  const [cc, setCc] = useState("");
  const [bcc, setBcc] = useState("");
  const [showCc, setShowCc] = useState(false);
  const [showBcc, setShowBcc] = useState(false);
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [attachments, setAttachments] = useState<File[]>([]);
  const [isSending, setIsSending] = useState(false);

  // Automatically close popup after success
  // useEffect removed since we use inline timeouts with sonner now

  const fileInputRef = useRef<HTMLInputElement>(null);

  const postScheduledEmail = async (isoString: string) => {
    setIsSending(true);
    const formData = new FormData();
    formData.append("email", email);
    formData.append("cc", cc);
    formData.append("bcc", bcc);
    formData.append("name", name);
    formData.append("company", company); 
    formData.append("subject", subject);
    formData.append("body", body);
    formData.append("scheduled_at", isoString);
    
    attachments.forEach((file) => {
      formData.append("attachments", file);
    });

    try {
      const response = await fetch(`${API_BASE}/single-send/schedule`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${getToken()}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || "Failed to schedule email");
      }
      
      const formattedDate = new Date(isoString).toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        dateStyle: 'medium',
        timeStyle: 'short'
      });
      toast.success(`Message scheduled successfully for ${formattedDate}!`);
      setTimeout(() => onClose(), 1500);
    } catch (error: any) {
      toast.error(error.message || "Failed to schedule email.");
    } finally {
      setIsSending(false);
    }
  };

  const handleSchedule = (timeType: string) => {
    // Validate required fields exactly like handleSend
    const isBodyEmpty = !body || body === "<p><br></p>" || body.trim() === "";
    if (!email || !name || !subject || isBodyEmpty) {
      toast.error("Please fill out all required fields (*).");
      return;
    }

    // Check total attachment size (25MB)
    const totalSize = attachments.reduce((acc, file) => acc + file.size, 0);
    if (totalSize > 25 * 1024 * 1024) {
      toast.error("Total attachments size exceeds 25MB limit.");
      return;
    }

    if (timeType === "Custom time and date") {
      setIsCustomScheduleOpen(true);
      return;
    }

    let scheduleDate = new Date();
    if (timeType.includes("Tomorrow")) {
      scheduleDate.setDate(scheduleDate.getDate() + 1);
      scheduleDate.setHours(9, 0, 0, 0);
    } else if (timeType.includes("Monday")) {
      const daysUntilMonday = (1 + 7 - scheduleDate.getDay()) % 7 || 7;
      scheduleDate.setDate(scheduleDate.getDate() + daysUntilMonday);
      scheduleDate.setHours(9, 0, 0, 0);
    }
    
    postScheduledEmail(scheduleDate.toISOString());
  };

  const handleConfirmCustomSchedule = () => {
    if (!customScheduleTime) {
      toast.error("Please select a valid date and time.");
      return;
    }
    const scheduleDate = new Date(customScheduleTime);
    setIsCustomScheduleOpen(false);
    postScheduledEmail(scheduleDate.toISOString());
  };

  const handleLinkClick = () => {
    if (quillRef.current) {
      const editor = quillRef.current.getEditor();
      const range = editor.getSelection();
      setLinkSelection(range);

      if (range && range.length > 0) {
        const text = editor.getText(range.index, range.length);
        setLinkText(text);
        
        const format = editor.getFormat(range.index, range.length);
        if (format.link) {
          setLinkUrl(format.link);
        } else {
          setLinkUrl("");
        }
      } else {
        setLinkText("");
        setLinkUrl("");
      }
      setIsLinkDialogOpen(true);
    }
  };

  const handleSaveLink = () => {
    if (quillRef.current) {
      const editor = quillRef.current.getEditor();
      
      // Ensure editor has focus to perform insertion
      editor.focus();
      
      let finalUrl = linkUrl.trim();
      if (finalUrl && !/^https?:\/\//i.test(finalUrl) && !/^mailto:/i.test(finalUrl)) {
        finalUrl = 'https://' + finalUrl;
      }

      if (linkSelection) {
        if (linkSelection.length > 0) {
          // Replace selected text
          editor.deleteText(linkSelection.index, linkSelection.length);
          editor.insertText(linkSelection.index, linkText || finalUrl, 'link', finalUrl);
          editor.setSelection(linkSelection.index + (linkText || finalUrl).length, 0);
        } else {
          // Insert new text
          editor.insertText(linkSelection.index, linkText || finalUrl, 'link', finalUrl);
          editor.setSelection(linkSelection.index + (linkText || finalUrl).length, 0);
        }
      } else {
        // Fallback if no selection was saved
        const range = editor.getSelection() || { index: editor.getLength(), length: 0 };
        editor.insertText(range.index, linkText || finalUrl, 'link', finalUrl);
      }
    }
    setIsLinkDialogOpen(false);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    const isBodyEmpty = !body || body === "<p><br></p>" || body.trim() === "";
    if (!email || !name || !subject || isBodyEmpty) {
      toast.error("Please fill out all required fields (*).");
      return;
    }

    // Check total attachment size (25MB)
    const totalSize = attachments.reduce((acc, file) => acc + file.size, 0);
    if (totalSize > 25 * 1024 * 1024) {
      toast.error("Total attachments size exceeds 25MB limit.");
      return;
    }

    setIsSending(true);

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

      const token = await getToken();

      const res = await fetch(`${API_BASE}/single-send`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData
      });

      const data = await res.json();

      if (res.ok && data.status === "success") {
        toast.success("Email sent successfully with tracking!");
        // Clear form
        setEmail("");
        setCc("");
        setBcc("");
        setName("");
        setCompany("");
        setSubject("");
        setBody("");
        setAttachments([]);
        
        // Dispatch custom event to notify Inbox tracking table
        window.dispatchEvent(new Event("refresh-inbox-tracking"));
        setTimeout(() => onClose(), 1500);
      } else {
        toast.error(data.message || "Failed to send email.");
      }
    } catch (err: any) {
      toast.error(err.message || "An error occurred.");
    }
    setIsSending(false);
  };

  return (
    <TooltipProvider delay={300}>
      <div
        className={`fixed bottom-0 right-12 z-50 w-[540px] max-w-[calc(100vw-48px)] shadow-2xl bg-white border border-gray-200 rounded-t-xl flex flex-col transition-all duration-300 ${
          isMinimized ? "h-12" : "h-[580px] max-h-[85vh]"
        }`}
      >
      {/* HEADER BAR */}
      <div
        onClick={() => setIsMinimized(!isMinimized)}
        className="h-12 px-4 bg-[#f2f6fc] border-b border-gray-200 flex items-center justify-between rounded-t-xl shrink-0 cursor-pointer select-none"
      >
        <span className="text-sm font-semibold text-black flex items-center gap-2">
          New message
        </span>
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <Tooltip>
            <TooltipTrigger
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1.5 text-gray-700 hover:text-black hover:bg-gray-200 rounded transition cursor-pointer outline-none flex items-center justify-center"
            >
              {isMinimized ? <Maximize2 size={13} /> : <Minus size={13} />}
            </TooltipTrigger>
            <TooltipContent><p>{isMinimized ? "Expand" : "Minimize"}</p></TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger
              onClick={handleCloseRequest}
              className="p-1.5 text-gray-700 hover:text-black hover:bg-gray-200 rounded transition cursor-pointer outline-none flex items-center justify-center"
            >
              <X size={13} />
            </TooltipTrigger>
            <TooltipContent><p>Close</p></TooltipContent>
          </Tooltip>
        </div>
      </div>

      {/* FORM BODY */}
      {!isMinimized && (
        <form onSubmit={handleSend} className="flex-1 flex flex-col min-h-0 bg-white text-gray-900">
          <div className="px-5 py-2 flex-1 overflow-y-auto custom-scrollbar flex flex-col space-y-0.5">
            {/* Recipient Email & Cc/Bcc Toggle */}
            <div className="border-b border-gray-200 py-2 flex items-center gap-2 shrink-0">
              <span className="text-gray-500 text-sm font-medium w-16 shrink-0">To <span className="text-red-500">*</span></span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 bg-transparent border-0 outline-none text-sm text-black placeholder-gray-400"
                placeholder="client@example.com"
              />
              <div className="flex items-center gap-2">
                {!showCc && (
                  <button
                    type="button"
                    onClick={() => setShowCc(true)}
                    className="text-xs text-gray-500 hover:text-gray-700 font-medium cursor-pointer"
                  >
                    Cc
                  </button>
                )}
                {!showBcc && (
                  <button
                    type="button"
                    onClick={() => setShowBcc(true)}
                    className="text-xs text-gray-500 hover:text-gray-700 font-medium cursor-pointer"
                  >
                    Bcc
                  </button>
                )}
              </div>
            </div>

            {/* CC / BCC fields */}
            {showCc && (
              <div className="border-b border-gray-200 py-2 flex items-center gap-2 shrink-0">
                <span className="text-gray-500 text-sm font-medium w-16 shrink-0">Cc</span>
                <input
                  type="text"
                  value={cc}
                  onChange={(e) => setCc(e.target.value)}
                  className="flex-1 bg-transparent border-0 outline-none text-sm text-black placeholder-gray-400"
                  placeholder="manager@example.com"
                />
              </div>
            )}
            {showBcc && (
              <div className="border-b border-gray-200 py-2 flex items-center gap-2 shrink-0">
                <span className="text-gray-500 text-sm font-medium w-16 shrink-0">Bcc</span>
                <input
                  type="text"
                  value={bcc}
                  onChange={(e) => setBcc(e.target.value)}
                  className="flex-1 bg-transparent border-0 outline-none text-sm text-black placeholder-gray-400"
                  placeholder="hidden@example.com"
                />
              </div>
            )}

            {/* Name Input */}
            <div className="border-b border-gray-200 py-2 flex items-center gap-2 shrink-0">
              <span className="text-gray-500 text-sm font-medium w-16 shrink-0">Name <span className="text-red-500">*</span></span>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="flex-1 bg-transparent border-0 outline-none text-sm text-black placeholder-gray-400"
                placeholder="John Doe"
              />
            </div>

            {/* Company Input */}
            <div className="border-b border-gray-200 py-2 flex items-center gap-2 shrink-0">
              <span className="text-gray-500 text-sm font-medium w-16 shrink-0">Company</span>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="flex-1 bg-transparent border-0 outline-none text-sm text-black placeholder-gray-400"
                placeholder="Acme Corp"
              />
            </div>

            {/* Subject Input */}
            <div className="border-b border-gray-200 py-2.5 flex items-center gap-2 shrink-0">
              <span className="text-gray-500 text-sm font-medium w-16 shrink-0">Subject <span className="text-red-500">*</span></span>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="flex-1 bg-transparent border-0 outline-none text-sm text-black placeholder-gray-400"
                placeholder="Email subject..."
              />
            </div>

            {/* Rich Editor */}
            <div className="flex-1 flex flex-col pt-3 min-h-[160px]">
              <div className="flex-1 bg-transparent text-gray-900 overflow-hidden flex flex-col">
                <ReactQuill
                  {...({ ref: quillRef } as any)}
                  theme="snow"
                  value={body}
                  onChange={setBody}
                  placeholder="Compose your email here... *"
                  className="flex-1 flex flex-col h-full light-quill"
                  modules={{
                    toolbar: {
                      container: "#quill-toolbar"
                    }
                  }}
                />
              </div>
            </div>

            {/* Custom Pill Toolbar Container */}
            <div className={`px-5 pb-2 shrink-0 bg-white transition-all ${showFormatting ? 'block' : 'hidden'}`}>
              <div className="inline-flex items-center rounded-xl bg-gray-50 border border-gray-200 shadow-sm p-1 overflow-x-auto max-w-full custom-scrollbar">
                <div id="quill-toolbar" className="!border-none !bg-transparent !p-0 flex items-center gap-0.5 whitespace-nowrap">
                  <select className="ql-font" defaultValue="">
                    <option value=""></option>
                    <option value="serif"></option>
                    <option value="monospace"></option>
                  </select>
                  <select className="ql-size" defaultValue="">
                    <option value="small"></option>
                    <option value=""></option>
                    <option value="large"></option>
                    <option value="huge"></option>
                  </select>
                  <div className="w-[1px] h-4 bg-gray-300 mx-1 shrink-0"></div>
                  <button className="ql-bold"></button>
                  <button className="ql-italic"></button>
                  <button className="ql-underline"></button>
                  <select className="ql-color"></select>
                  <div className="w-[1px] h-4 bg-gray-300 mx-1 shrink-0"></div>
                  <select className="ql-align"></select>
                  <button className="ql-list" value="ordered"></button>
                  <button className="ql-list" value="bullet"></button>
                  <div className="w-[1px] h-4 bg-gray-300 mx-1 shrink-0"></div>
                  <button className="ql-code-block"></button>
                  <button className="ql-blockquote"></button>
                  <button className="ql-clean"></button>
                </div>
              </div>
            </div>

            {/* File Attachments list */}
            {attachments.length > 0 && (
              <div className="flex flex-wrap gap-2 py-3 border-t border-gray-100 shrink-0">
                {attachments.map((file, idx) => (
                  <div key={idx} className="flex items-center gap-2 bg-gray-100 border border-gray-200 px-2.5 py-1 rounded-lg text-xs text-gray-700">
                    <span className="truncate max-w-[150px]">{file.name}</span>
                    <span className="text-[10px] text-gray-500">{(file.size / 1024 / 1024).toFixed(1)}MB</span>
                    <button
                      type="button"
                      onClick={() => setAttachments(attachments.filter((_, i) => i !== idx))}
                      className="text-gray-500 hover:text-red-500 transition-colors cursor-pointer"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}

          </div>

          {/* ACTION BAR */}
          <div className="h-16 px-5 bg-white flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              {/* Send Button Group */}
              <div className="flex items-center rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition active:scale-[0.98]">
                <button
                  type="submit"
                  disabled={isSending}
                  className="pl-5 pr-4 py-2.5 text-sm font-semibold rounded-l-full flex items-center gap-2 border-r border-blue-700 disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
                >
                  {isSending ? (
                    <><RefreshCw size={14} className="animate-spin" /> Sending...</>
                  ) : (
                    "Send"
                  )}
                </button>
                <DropdownMenu>
                  <DropdownMenuTrigger 
                    className="px-2.5 py-2.5 rounded-r-full hover:bg-blue-700/80 transition cursor-pointer outline-none flex items-center justify-center"
                  >
                    <ChevronDown size={14} />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent side="top" align="start" className="w-56 p-2 rounded-2xl shadow-xl border border-gray-100 mb-2 z-50 bg-white">
                    <DropdownMenuGroup>
                      <DropdownMenuLabel className="font-bold text-[15px] pb-3 pt-2 px-3 text-gray-900">
                        Schedule message
                      </DropdownMenuLabel>
                      <DropdownMenuItem className="py-2.5 px-3 text-[14px] text-gray-700 cursor-pointer focus:bg-gray-100 focus:text-gray-900 rounded-xl outline-none" onClick={() => handleSchedule("Tomorrow at 9:00 AM")}>
                        Tomorrow at 9:00 AM
                      </DropdownMenuItem>
                      <DropdownMenuItem className="py-2.5 px-3 text-[14px] text-gray-700 cursor-pointer focus:bg-gray-100 focus:text-gray-900 rounded-xl outline-none" onClick={() => handleSchedule("Monday at 9:00 AM")}>
                        Monday at 9:00 AM
                      </DropdownMenuItem>
                      <DropdownMenuItem className="py-2.5 px-3 text-[14px] text-gray-700 cursor-pointer focus:bg-gray-100 focus:text-gray-900 rounded-xl outline-none" onClick={() => handleSchedule("Custom time and date")}>
                        Custom time and date
                      </DropdownMenuItem>
                    </DropdownMenuGroup>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Formatting, Attach, Link Icons */}
              <div className="flex items-center gap-1 ml-2">
                <Tooltip>
                  <TooltipTrigger
                    onClick={() => setShowFormatting(!showFormatting)}
                    className={`p-2 rounded-full cursor-pointer flex items-center justify-center transition-colors outline-none ${showFormatting ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'}`}
                  >
                    <Type size={18} />
                  </TooltipTrigger>
                  <TooltipContent><p>Formatting options</p></TooltipContent>
                </Tooltip>

                <input
                  type="file"
                  multiple
                  ref={fileInputRef}
                  onChange={(e) => {
                    const files = e.target.files;
                    if (files) {
                      setAttachments(prev => [...prev, ...Array.from(files)]);
                    }
                  }}
                  className="hidden"
                />
                <Tooltip>
                  <TooltipTrigger
                    onClick={() => fileInputRef.current?.click()}
                    className="p-2 rounded-full text-gray-500 hover:text-gray-900 hover:bg-gray-100 cursor-pointer flex items-center justify-center transition-colors outline-none"
                  >
                    <Paperclip size={18} />
                  </TooltipTrigger>
                  <TooltipContent><p>Attach files</p></TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger
                    onClick={handleLinkClick}
                    className="p-2 rounded-full text-gray-500 hover:text-gray-900 hover:bg-gray-100 cursor-pointer flex items-center justify-center transition-colors outline-none"
                  >
                    <Link2 size={18} />
                  </TooltipTrigger>
                  <TooltipContent><p>Insert link</p></TooltipContent>
                </Tooltip>
              </div>
            </div>

            {/* Trash/Discard Button */}
            <Tooltip>
              <TooltipTrigger
                onClick={onClose}
                className="p-2.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors cursor-pointer outline-none flex items-center justify-center"
              >
                <Trash2 size={18} />
              </TooltipTrigger>
              <TooltipContent><p>Discard draft</p></TooltipContent>
            </Tooltip>
          </div>
        </form>
      )}

      {/* Custom Link Dialog */}
      <Dialog open={isLinkDialogOpen} onOpenChange={setIsLinkDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Add Link</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="linkText" className="text-right text-gray-600">
                Text to display
              </Label>
              <Input
                id="linkText"
                value={linkText}
                onChange={(e) => setLinkText(e.target.value)}
                placeholder="Click here..."
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="linkUrl" className="text-right text-gray-600">
                Link URL
              </Label>
              <Input
                id="linkUrl"
                value={linkUrl}
                onChange={(e) => setLinkUrl(e.target.value)}
                placeholder="https://example.com"
                className="col-span-3"
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setIsLinkDialogOpen(false)}>
              Cancel
            </Button>
            <Button type="button" className="bg-blue-600 hover:bg-blue-700 text-white" onClick={handleSaveLink}>
              Save Link
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Custom Schedule Dialog */}
      <Dialog open={isCustomScheduleOpen} onOpenChange={setIsCustomScheduleOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Custom Schedule</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="schedule-time" className="text-gray-700">Select Date and Time</Label>
              <Input
                id="schedule-time"
                type="datetime-local"
                value={customScheduleTime}
                onChange={(e) => setCustomScheduleTime(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setIsCustomScheduleOpen(false)}>
              Cancel
            </Button>
            <Button type="button" className="bg-blue-600 hover:bg-blue-700 text-white" onClick={handleConfirmCustomSchedule}>
              Schedule
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Exit Confirmation Dialog */}
      <Dialog open={showExitConfirm} onOpenChange={setShowExitConfirm}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Discard Draft?</DialogTitle>
          </DialogHeader>
          <div className="py-2 text-gray-600">
            You have unsaved changes. Are you sure you want to discard this email?
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setShowExitConfirm(false)}>
              Cancel
            </Button>
            <Button type="button" variant="destructive" onClick={onClose}>
              Discard
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      </div>
    </TooltipProvider>
  );
}
