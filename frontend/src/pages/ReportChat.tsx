import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import {
  getReport,
  listChatMessages,
  sendChatMessage,
  type ChatMessage,
  type ReportDetail,
} from "../api/reports";
import ChatBox from "../components/ChatBox";

export default function ReportChat() {
  const { t } = useTranslation();
  const { id } = useParams();
  const reportId = Number(id);
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);

  const suggestedPrompts = useMemo(
    () =>
      report?.has_analysis
        ? [
            t("reportAnalysis.chat.prompts.summary"),
            t("reportAnalysis.chat.prompts.revenue"),
            t("reportAnalysis.chat.prompts.risks"),
            t("reportAnalysis.chat.prompts.recommendations"),
          ]
        : [],
    [report?.has_analysis, t]
  );

  useEffect(() => {
    if (!reportId) return;
    void (async () => {
      try {
        const [r, m] = await Promise.all([getReport(reportId), listChatMessages(reportId)]);
        setReport(r);
        setMessages(m);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("errors.loadChat"));
      }
    })();
  }, [reportId, t]);

  const handleSend = async (message: string) => {
    setError(null);
    try {
      const result = await sendChatMessage(reportId, message);
      setMessages((prev) => [...prev, result.user_message, result.assistant_message]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.chatFailed"));
      throw err;
    }
  };

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>{t("reportChat.title")}</h1>
      {report && (
        <p className="muted">
          {report.original_filename} · <Link to={`/reports/${report.id}`}>{t("common.backToReport")}</Link>
          {report.has_analysis && (
            <>
              {" · "}
              <Link to={`/reports/${report.id}/analysis`}>{t("reportDetails.discussAnalysis")}</Link>
            </>
          )}
          {" · "}
          {report.has_analysis ? t("reportChat.hintWithAnalysis") : t("reportChat.hint")}.
        </p>
      )}
      {error && <div className="error">{error}</div>}
      <ChatBox
        messages={messages}
        onSend={handleSend}
        placeholder={report?.has_analysis ? t("reportAnalysis.chat.placeholder") : t("reportChat.placeholder")}
        emptyHint={report?.has_analysis ? t("reportAnalysis.chat.emptyHint") : t("reportChat.emptyHint")}
        suggestedPrompts={suggestedPrompts}
      />
    </div>
  );
}
