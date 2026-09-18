import { useEffect, useRef, useState } from "react";
import { Send, MessageSquare } from "lucide-react";
import { careApi } from "@/api";
import { useAppSelector } from "@/hooks/redux";
import type { DirectConversationItem, DirectMessageItem, DoctorPublic } from "@/types";

export default function Messages() {
  const { user } = useAppSelector((s) => s.auth);
  const [conversations, setConversations] = useState<DirectConversationItem[]>([]);
  const [doctors, setDoctors] = useState<DoctorPublic[]>([]);
  const [activeConvo, setActiveConvo] = useState<DirectConversationItem | null>(null);
  const [messages, setMessages] = useState<DirectMessageItem[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  function refreshConversations() {
    careApi.listConversations().then(setConversations);
  }

  useEffect(() => {
    refreshConversations();
    if (user?.role === "patient") careApi.listDoctors().then(setDoctors);
  }, [user]);

  useEffect(() => {
    if (activeConvo) careApi.getMessages(activeConvo.id).then(setMessages);
  }, [activeConvo]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function otherPartyId(convo: DirectConversationItem): string {
    return user?.role === "doctor" ? convo.patient_id : convo.doctor_id;
  }

  async function handleSend() {
    if (!input.trim() || !activeConvo) return;
    const text = input;
    setInput("");
    await careApi.sendMessage(otherPartyId(activeConvo), text);
    careApi.getMessages(activeConvo.id).then(setMessages);
    refreshConversations();
  }

  async function startConversationWithDoctor(doctorId: string) {
    await careApi.sendMessage(doctorId, "Hello, I'd like to connect.");
    const list = await careApi.listConversations();
    setConversations(list);
    const found = list.find((c) => c.doctor_id === doctorId);
    if (found) setActiveConvo(found);
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-7rem)] max-w-4xl gap-4">
      <div className="w-64 shrink-0 overflow-y-auto">
        <h2 className="mb-3 font-display text-lg font-bold text-slate-900 dark:text-white">Messages</h2>

        {user?.role === "patient" && doctors.length > 0 && (
          <div className="mb-4">
            <p className="mb-2 text-xs font-semibold text-slate-400">Start a new conversation</p>
            <select
              className="input-field text-xs"
              onChange={(e) => e.target.value && startConversationWithDoctor(e.target.value)}
              defaultValue=""
            >
              <option value="" disabled>
                Choose a doctor...
              </option>
              {doctors.map((d) => (
                <option key={d.user_id} value={d.user_id}>
                  Dr. {d.full_name}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="space-y-1">
          {conversations.map((c) => (
            <button
              key={c.id}
              onClick={() => setActiveConvo(c)}
              className={
                activeConvo?.id === c.id
                  ? "w-full rounded-xl bg-brand-50 p-3 text-left dark:bg-brand-900/30"
                  : "w-full rounded-xl p-3 text-left hover:bg-slate-100 dark:hover:bg-slate-800"
              }
            >
              <p className="truncate text-sm font-semibold text-slate-800 dark:text-slate-200">
                {c.other_party_name ?? "Conversation"}
              </p>
              {c.last_message && <p className="truncate text-xs text-slate-400">{c.last_message}</p>}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-1 flex-col rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        {!activeConvo ? (
          <div className="flex flex-1 flex-col items-center justify-center text-slate-400">
            <MessageSquare size={32} className="mb-2" />
            <p className="text-sm">Select a conversation</p>
          </div>
        ) : (
          <>
            <div className="flex-1 space-y-3 overflow-y-auto p-4">
              {messages.map((m) => (
                <div key={m.id} className={m.sender_id === user?.id ? "flex justify-end" : "flex justify-start"}>
                  <div
                    className={
                      m.sender_id === user?.id
                        ? "max-w-[75%] rounded-2xl rounded-br-sm bg-brand-600 px-4 py-2 text-sm text-white"
                        : "max-w-[75%] rounded-2xl rounded-bl-sm bg-slate-100 px-4 py-2 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-200"
                    }
                  >
                    {m.content}
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
            <div className="flex items-center gap-2 border-t border-slate-100 p-3 dark:border-slate-800">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                className="input-field"
                placeholder="Type a message..."
              />
              <button onClick={handleSend} className="btn-primary px-4">
                <Send size={16} />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
