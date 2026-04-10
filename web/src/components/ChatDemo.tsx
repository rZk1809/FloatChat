"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, Sparkles } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const EXAMPLE_QUERIES = [
  "What is a T-S diagram and how does FloatChat generate them?",
  "Explain the temperature profile of the Bay of Bengal",
  "How does the multi-agent RAG system work?",
  "What patterns did clustering reveal in the ARGO data?",
  "What is the thermocline depth in the Arabian Sea?",
];

export default function ChatDemo() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm **FloatChat**, your AI assistant for oceanographic data analysis. I can answer questions about ARGO float data, ocean dynamics in the Indian Ocean, Bay of Bengal, and Arabian Sea, as well as the multi-agent AI system powering this platform.\n\nTry asking me anything about ocean science or the FloatChat system!",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: content.trim() };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: newMessages.filter((m) => m.role !== "assistant" || newMessages.indexOf(m) > 0).slice(-10),
        }),
      });

      const data = await response.json();

      if (data.error) {
        setMessages([
          ...newMessages,
          {
            role: "assistant",
            content: `**System Notice:** ${data.error}\n\nThe chat demo requires an Anthropic API key to be configured. The FloatChat system architecture and all visualizations are still fully available above.`,
          },
        ]);
      } else {
        setMessages([
          ...newMessages,
          { role: "assistant", content: data.content },
        ]);
      }
    } catch {
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content:
            "I encountered an error connecting to the AI service. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const renderMessage = (text: string) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/`(.*?)`/g, '<code class="bg-ocean-700 px-1 rounded text-cyan-400 text-sm font-mono">$1</code>')
      .replace(/\n/g, "<br/>");
  };

  return (
    <div className="flex flex-col h-[600px] glass rounded-2xl overflow-hidden">
      {/* Chat header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-cyan-500/10 bg-ocean-800/50">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
          <Bot size={20} className="text-white" />
        </div>
        <div>
          <p className="font-semibold text-white">FloatChat Assistant</p>
          <div className="flex items-center gap-2">
            <div className="pulse-dot" style={{ width: 8, height: 8 }}></div>
            <p className="text-xs text-cyan-400">Powered by Claude AI</p>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-1.5 text-xs text-slate-400 bg-ocean-700/50 px-3 py-1.5 rounded-full">
          <Sparkles size={12} className="text-cyan-400" />
          Live Demo
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`chat-message flex gap-3 ${
              msg.role === "user" ? "flex-row-reverse" : ""
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                msg.role === "assistant"
                  ? "bg-gradient-to-br from-cyan-500 to-blue-600"
                  : "bg-gradient-to-br from-slate-600 to-slate-700"
              }`}
            >
              {msg.role === "assistant" ? (
                <Bot size={16} className="text-white" />
              ) : (
                <User size={16} className="text-white" />
              )}
            </div>
            <div
              className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-gradient-to-br from-cyan-600/90 to-blue-700/90 text-white rounded-tr-sm"
                  : "bg-ocean-700/70 text-slate-200 rounded-tl-sm border border-cyan-500/10"
              }`}
              dangerouslySetInnerHTML={{ __html: renderMessage(msg.content) }}
            />
          </div>
        ))}

        {isLoading && (
          <div className="chat-message flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex-shrink-0 flex items-center justify-center">
              <Bot size={16} className="text-white" />
            </div>
            <div className="bg-ocean-700/70 border border-cyan-500/10 px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-2">
              <span className="typing-dot w-2 h-2 bg-cyan-400 rounded-full inline-block" />
              <span className="typing-dot w-2 h-2 bg-cyan-400 rounded-full inline-block" />
              <span className="typing-dot w-2 h-2 bg-cyan-400 rounded-full inline-block" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Example queries */}
      {messages.length <= 1 && (
        <div className="px-4 pb-2">
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
      <div className="px-4 pb-4 pt-2 border-t border-cyan-500/10">
        <div className="flex gap-2 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about ocean data, ARGO floats, or the FloatChat system..."
            rows={1}
            className="flex-1 bg-ocean-700/50 border border-cyan-500/20 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 resize-none focus:outline-none focus:border-cyan-500/50 focus:bg-ocean-700/70 transition-all duration-200 max-h-32"
            style={{ minHeight: "48px" }}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isLoading}
            className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center hover:from-cyan-400 hover:to-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 flex-shrink-0"
          >
            {isLoading ? (
              <Loader2 size={18} className="text-white animate-spin" />
            ) : (
              <Send size={18} className="text-white" />
            )}
          </button>
        </div>
        <p className="text-xs text-slate-600 mt-2 px-1">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
