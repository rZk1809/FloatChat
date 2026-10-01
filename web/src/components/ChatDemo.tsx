"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Bot,
  User,
  Loader2,
  Sparkles,
  History,
  Download,
  X,
  Clock,
  Trash2,
} from "lucide-react";
import MessageContent from "./MessageContent";
import CopyButton from "./CopyButton";
import ToastContainer from "./Toast";
import { useQueryHistory } from "@/hooks/useQueryHistory";
import { useToast } from "@/hooks/useToast";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

const EXAMPLE_QUERIES = [
  "What is a T-S diagram and how does FloatChat generate them?",
  "Explain the temperature profile of the Bay of Bengal",
  "How does the multi-agent RAG system work?",
  "What patterns did clustering reveal in the ARGO data?",
  "What is the thermocline depth in the Arabian Sea?",
];

const FOLLOW_UP_MAP: [string, string[]][] = [
  ["t-s diagram", ["What do the 4 clusters in the T-S diagram represent?", "How is seawater density overlaid on a T-S diagram?"]],
  ["bay of bengal", ["How does Bay of Bengal salinity compare to Arabian Sea?", "What is the mixed layer depth in Bay of Bengal?"]],
  ["arabian sea", ["What drives the high salinity in the Arabian Sea?", "How does Arabian Sea temperature vary with depth?"]],
  ["multi-agent", ["What does the Planner agent specifically parse?", "How does the Executor agent call tools?"]],
  ["clustering", ["What are the 4 water mass clusters identified?", "How was the optimal k=4 determined?"]],
  ["thermocline", ["What causes seasonal thermocline shoaling?", "How does thermocline depth affect mixing?"]],
  ["xgboost", ["What features does XGBoost use for temperature prediction?", "How is the R²=0.97 score interpreted?"]],
  ["anomal", ["How does Isolation Forest detect anomalous profiles?", "What physical causes produce anomalous ARGO readings?"]],
];

function getFollowUps(lastMessage: string): string[] {
  const lower = lastMessage.toLowerCase();
  for (const [key, followUps] of FOLLOW_UP_MAP) {
    if (lower.includes(key)) return followUps;
  }
  return [
    "What else can FloatChat analyze?",
    "How does ARGO data help predict monsoons?",
  ];
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function exportAsMarkdown(messages: Message[]): string {
  const lines = ["# FloatChat Conversation Export", "", `_Exported ${new Date().toLocaleString()}_`, ""];
  for (const m of messages) {
    lines.push(`## ${m.role === "user" ? "You" : "FloatChat"} — ${formatTime(m.timestamp)}`);
    lines.push("", m.content, "");
  }
  return lines.join("\n");
}

function downloadText(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ChatDemo() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm **FloatChat**, your AI assistant for oceanographic data analysis. I can answer questions about ARGO float data, ocean dynamics in the Indian Ocean, Bay of Bengal, and Arabian Sea, as well as the multi-agent AI system powering this platform.\n\nTry asking me anything about ocean science or the FloatChat system!",
      timestamp: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [followUps, setFollowUps] = useState<string[]>([]);
  const [charLimit] = useState(4000);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const { history, addToHistory, removeFromHistory, clearHistory } = useQueryHistory();
  const { toasts, addToast, removeToast } = useToast();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
        inputRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      const userMessage: Message = { role: "user", content: content.trim(), timestamp: Date.now() };
      const newMessages = [...messages, userMessage];
      setMessages(newMessages);
      setInput("");
      setIsLoading(true);
      setFollowUps([]);

      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: newMessages
              .filter((m) => m.role !== "assistant" || newMessages.indexOf(m) > 0)
              .slice(-10)
              .map(({ role, content }) => ({ role, content })),
          }),
        });

        const data = await response.json() as { content?: string; error?: string };

        if (data.error) {
          setMessages([
            ...newMessages,
            {
              role: "assistant",
              content: `**System Notice:** ${data.error}\n\nThe chat demo requires an API key to be configured. The FloatChat system architecture and all visualizations are still fully available above.`,
              timestamp: Date.now(),
            },
          ]);
        } else {
          const assistantContent = data.content ?? "Unable to generate response.";
          setMessages([
            ...newMessages,
            { role: "assistant", content: assistantContent, timestamp: Date.now() },
          ]);
          addToHistory(content.trim(), assistantContent);
          setFollowUps(getFollowUps(assistantContent));
        }
      } catch {
        setMessages([
          ...newMessages,
          {
            role: "assistant",
            content: "I encountered an error connecting to the AI service. Please try again.",
            timestamp: Date.now(),
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [messages, isLoading, addToHistory]
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const handleExportMarkdown = () => {
    downloadText(exportAsMarkdown(messages), "floatchat-conversation.md", "text/markdown");
    addToast("Conversation exported as Markdown", "success");
  };

  const handleExportJSON = () => {
    downloadText(JSON.stringify(messages, null, 2), "floatchat-conversation.json", "application/json");
    addToast("Conversation exported as JSON", "success");
  };

  const handleClearChat = () => {
    setMessages([
      {
        role: "assistant",
        content: "Chat cleared! Feel free to ask me anything about ocean science or the FloatChat system.",
        timestamp: Date.now(),
      },
    ]);
    setFollowUps([]);
    addToast("Chat cleared", "info");
  };

  const charCount = input.length;
  const charPct = (charCount / charLimit) * 100;

  return (
    <>
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      <div className="flex flex-col h-[600px] glass rounded-2xl overflow-hidden relative">
        {/* History panel */}
        {showHistory && (
          <div className="absolute inset-0 z-10 bg-ocean-900/95 backdrop-blur-sm flex flex-col">
            <div className="flex items-center justify-between px-5 py-3 border-b border-cyan-500/10">
              <h3 className="font-semibold text-white text-sm flex items-center gap-2">
                <History size={14} className="text-cyan-400" />
                Query History
              </h3>
              <div className="flex items-center gap-2">
                {history.length > 0 && (
                  <button
                    onClick={clearHistory}
                    className="text-xs text-slate-500 hover:text-red-400 transition-colors flex items-center gap-1"
                  >
                    <Trash2 size={12} />
                    Clear all
                  </button>
                )}
                <button
                  onClick={() => setShowHistory(false)}
                  className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-white hover:bg-ocean-600/60"
                  aria-label="Close history"
                >
                  <X size={14} />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {history.length === 0 ? (
                <p className="text-slate-500 text-sm text-center py-8">No query history yet</p>
              ) : (
                history.map((item) => (
                  <div key={item.id} className="group flex gap-2">
                    <button
                      onClick={() => {
                        sendMessage(item.query);
                        setShowHistory(false);
                      }}
                      className="flex-1 text-left px-3 py-2.5 rounded-lg bg-ocean-700/50 border border-cyan-500/10 hover:border-cyan-500/30 transition-all"
                    >
                      <p className="text-xs text-slate-300 font-medium truncate">{item.query}</p>
                      {item.responseSnippet && (
                        <p className="text-xs text-slate-600 mt-0.5 truncate">{item.responseSnippet}…</p>
                      )}
                      <p className="text-xs text-slate-600 mt-1 flex items-center gap-1">
                        <Clock size={10} />
                        {formatTime(item.timestamp)}
                      </p>
                    </button>
                    <button
                      onClick={() => removeFromHistory(item.id)}
                      className="opacity-0 group-hover:opacity-100 w-7 h-7 flex-shrink-0 rounded flex items-center justify-center text-slate-600 hover:text-red-400 transition-all self-start mt-1"
                      aria-label="Remove from history"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Chat header */}
        <div className="flex items-center gap-3 px-5 py-3.5 border-b border-cyan-500/10 bg-ocean-800/50 flex-shrink-0">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
            <Bot size={18} className="text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-white text-sm">FloatChat Assistant</p>
            <div className="flex items-center gap-2">
              <div className="pulse-dot" style={{ width: 7, height: 7 }} />
              <p className="text-xs text-cyan-400">Powered by AI</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="relative w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-cyan-300 hover:bg-ocean-600/60 transition-colors"
              aria-label="Query history"
              title="Query history"
            >
              <History size={15} />
              {history.length > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-cyan-500 text-[9px] text-white flex items-center justify-center font-bold">
                  {history.length > 9 ? "9+" : history.length}
                </span>
              )}
            </button>
            <div className="relative group">
              <button
                className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-cyan-300 hover:bg-ocean-600/60 transition-colors"
                aria-label="Export conversation"
                title="Export"
              >
                <Download size={15} />
              </button>
              <div className="absolute right-0 top-9 hidden group-hover:block z-20 bg-ocean-800 border border-cyan-500/20 rounded-lg overflow-hidden shadow-xl min-w-[140px]">
                <button
                  onClick={handleExportMarkdown}
                  className="w-full text-left px-3 py-2 text-xs text-slate-300 hover:bg-ocean-700 hover:text-white transition-colors"
                >
                  Export as Markdown
                </button>
                <button
                  onClick={handleExportJSON}
                  className="w-full text-left px-3 py-2 text-xs text-slate-300 hover:bg-ocean-700 hover:text-white transition-colors"
                >
                  Export as JSON
                </button>
                <button
                  onClick={handleClearChat}
                  className="w-full text-left px-3 py-2 text-xs text-red-400 hover:bg-ocean-700 hover:text-red-300 transition-colors border-t border-slate-700/50"
                >
                  Clear Chat
                </button>
              </div>
            </div>
            <div className="ml-1 flex items-center gap-1 text-xs text-slate-500 bg-ocean-700/50 px-2.5 py-1 rounded-full">
              <Sparkles size={11} className="text-cyan-400" />
              Live
            </div>
          </div>
        </div>

        {/* Messages */}
        <div
          className="flex-1 overflow-y-auto p-4 space-y-4"
          role="log"
          aria-live="polite"
          aria-relevant="additions"
        >
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`chat-message flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                  msg.role === "assistant"
                    ? "bg-gradient-to-br from-cyan-500 to-blue-600"
                    : "bg-gradient-to-br from-slate-600 to-slate-700"
                }`}
              >
                {msg.role === "assistant" ? (
                  <Bot size={15} className="text-white" />
                ) : (
                  <User size={15} className="text-white" />
                )}
              </div>
              <div className={`flex flex-col gap-1 max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                <div
                  className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-gradient-to-br from-cyan-600/90 to-blue-700/90 text-white rounded-tr-sm"
                      : "bg-ocean-700/70 text-slate-200 rounded-tl-sm border border-cyan-500/10"
                  }`}
                >
                  <MessageContent content={msg.content} />
                </div>
                <div className={`flex items-center gap-1.5 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                  <span className="text-[10px] text-slate-600">{formatTime(msg.timestamp)}</span>
                  {msg.role === "assistant" && (
                    <CopyButton text={msg.content} size={12} className="w-5 h-5" />
                  )}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="chat-message flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex-shrink-0 flex items-center justify-center">
                <Bot size={15} className="text-white" />
              </div>
              <div className="bg-ocean-700/70 border border-cyan-500/10 px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-2">
                <span className="typing-dot w-2 h-2 bg-cyan-400 rounded-full inline-block" />
                <span className="typing-dot w-2 h-2 bg-cyan-400 rounded-full inline-block" />
                <span className="typing-dot w-2 h-2 bg-cyan-400 rounded-full inline-block" />
              </div>
            </div>
          )}

          {/* Suggested follow-ups */}
          {followUps.length > 0 && !isLoading && (
            <div className="flex flex-wrap gap-2 pl-11">
              {followUps.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="text-xs px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 hover:border-cyan-500/40 hover:bg-cyan-500/15 transition-all duration-200"
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Example queries */}
        {messages.length <= 1 && !isLoading && (
          <div className="px-4 pb-2 flex-shrink-0">
            <p className="text-xs text-slate-500 mb-2 px-1">Try an example:</p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_QUERIES.slice(0, 3).map((q, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(q)}
                  className="text-xs px-3 py-1.5 rounded-full bg-ocean-700/60 border border-cyan-500/15 text-cyan-300 hover:border-cyan-500/40 hover:bg-ocean-600/60 transition-all duration-200"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="px-4 pb-4 pt-2 border-t border-cyan-500/10 flex-shrink-0">
          <div className="flex gap-2 items-end">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about ocean data, ARGO floats, or the FloatChat system..."
                rows={1}
                aria-label="Message input"
                maxLength={charLimit}
                className="w-full bg-ocean-700/50 border border-cyan-500/20 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 resize-none focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-ocean-800 focus:border-cyan-500/50 focus:bg-ocean-700/70 transition-all duration-200 max-h-32"
                style={{ minHeight: "48px" }}
              />
              {charCount > charLimit * 0.7 && (
                <span
                  className={`absolute bottom-2 right-2 text-[10px] ${
                    charCount >= charLimit ? "text-red-400" : "text-slate-500"
                  }`}
                >
                  {charCount}/{charLimit}
                </span>
              )}
            </div>
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || isLoading || charCount > charLimit}
              aria-label="Send message"
              className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center hover:from-cyan-400 hover:to-blue-500 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-ocean-900 transition-all duration-200 flex-shrink-0"
            >
              {isLoading ? (
                <Loader2 size={18} className="text-white animate-spin" />
              ) : (
                <Send size={18} className="text-white" />
              )}
            </button>
          </div>
          <p className="text-xs text-slate-600 mt-2 px-1">
            Enter to send · Shift+Enter for new line · ⌘K to focus
          </p>
        </div>
      </div>
    </>
  );
}
