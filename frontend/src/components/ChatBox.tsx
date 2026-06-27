import { FormEvent, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

export interface ChatMessageLike {
  id: number;
  role: "user" | "assistant";
  content: string;
}

interface Props {
  messages: ChatMessageLike[];
  onSend: (message: string) => Promise<void>;
  disabled?: boolean;
  placeholder?: string;
  emptyHint?: string;
  suggestedPrompts?: string[];
}

export default function ChatBox({
  messages,
  onSend,
  disabled,
  placeholder,
  emptyHint,
  suggestedPrompts = [],
}: Props) {
  const { t, i18n } = useTranslation();
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const isRtl = i18n.language === "ar";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || sending || disabled) return;
    setSending(true);
    try {
      await onSend(trimmed);
      setInput("");
    } finally {
      setSending(false);
    }
  };

  const handlePrompt = async (prompt: string) => {
    if (sending || disabled) return;
    setSending(true);
    try {
      await onSend(prompt);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="card chat-box">
      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="muted">{emptyHint ?? t("reportChat.emptyHint")}</p>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`chat-message-row ${msg.role === "user" ? "chat-message-user" : "chat-message-assistant"}`}
            style={{ textAlign: msg.role === "user" ? (isRtl ? "left" : "right") : isRtl ? "right" : "left" }}
          >
            <div className={`chat-bubble chat-bubble-${msg.role}`}>{msg.content}</div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      {suggestedPrompts.length > 0 && messages.length === 0 && (
        <div className="chat-suggestions">
          {suggestedPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="chat-suggestion-btn"
              disabled={disabled || sending}
              onClick={() => void handlePrompt(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>
      )}
      <form className="chat-form" onSubmit={(e) => void handleSubmit(e)}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder ?? t("reportChat.placeholder")}
          disabled={disabled || sending}
          className="chat-input"
        />
        <button className="btn" type="submit" disabled={disabled || sending || !input.trim()}>
          {t("common.send")}
        </button>
      </form>
    </div>
  );
}
