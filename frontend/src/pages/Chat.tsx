import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Send, Sparkles, BookOpen } from "lucide-react";
import { useTranslation } from "react-i18next";
import { chatApi } from "@/api";
import { extractErrorMessage } from "@/api/client";
import type { ChatMessageOut } from "@/types";
import DisclaimerBanner from "@/components/DisclaimerBanner";

export default function Chat() {
  const { t } = useTranslation();
  const [messages, setMessages] = useState<ChatMessageOut[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    setInput(""); setError(null);

    const optimistic: ChatMessageOut = {
      id: `temp-${Date.now()}`, role: "user", content: text,
      retrieved_sources: [], used_fallback: false, created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimistic]);
    setLoading(true);

    try {
      const data = await chatApi.send(text, conversationId);
      setConversationId(data.conversation_id);
      setMessages((prev) => [...prev.slice(0, -1), data.user_message, data.assistant_message]);
    } catch (err) { setError(extractErrorMessage(err)); }
    finally { setLoading(false); }
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-7rem)] max-w-3xl flex-col gap-3">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">{t("chat.title")}</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">{t("chat.subtitle")}</p>
      </div>
      <DisclaimerBanner compact />

      <div className="flex-1 space-y-4 overflow-y-auto pr-1">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-slate-400">
            <Sparkles size={32} className="mb-3" />
            <p className="text-sm">{t("chat.empty_state")}</p>
          </div>
        )}
        {messages.map((m) => (
          <motion.div key={m.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            className={m.role === "user" ? "flex justify-end" : "flex justify-start"}
          >
            <div className={m.role === "user"
              ? "max-w-[80%] rounded-2xl rounded-br-sm bg-brand-600 px-4 py-2.5 text-sm text-white"
              : "max-w-[80%] rounded-2xl rounded-bl-sm bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm dark:bg-slate-800 dark:text-slate-200"
            }>
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.retrieved_sources.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5 border-t border-slate-100 pt-2 dark:border-slate-700">
                  {m.retrieved_sources.map((s) => (
                    <span key={s.source_id + s.title}
                      className="flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500 dark:bg-slate-700 dark:text-slate-400"
                      title={s.snippet}
                    >
                      <BookOpen size={10} />{s.title}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-sm bg-white px-4 py-3 shadow-sm dark:bg-slate-800">
              <div className="flex gap-1">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="flex items-center gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          className="input-field" placeholder={t("chat.placeholder")} />
        <button onClick={handleSend} disabled={loading || !input.trim()} className="btn-primary px-4">
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
