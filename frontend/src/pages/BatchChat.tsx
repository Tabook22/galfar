import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import {
  getBatch,
  getLatestBatchAnalysis,
  listBatchChatMessages,
  sendBatchChatMessage,
  type BatchAnalysis,
  type BatchChatMessage,
  type BatchDetail,
} from "../api/batches";
import ChatBox from "../components/ChatBox";

export default function BatchChat() {
  const { t } = useTranslation();
  const { id } = useParams();
  const batchId = Number(id);
  const [batch, setBatch] = useState<BatchDetail | null>(null);
  const [analysis, setAnalysis] = useState<BatchAnalysis | null>(null);
  const [messages, setMessages] = useState<BatchChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);

  const hasAnalysis = analysis?.status === "completed";

  const suggestedPrompts = useMemo(
    () =>
      hasAnalysis
        ? [
            t("batch.analysis.chat.prompts.summary"),
            t("batch.analysis.chat.prompts.revenue"),
            t("batch.analysis.chat.prompts.compare"),
            t("batch.analysis.chat.prompts.risks"),
          ]
        : [],
    [hasAnalysis, t]
  );

  useEffect(() => {
    if (!batchId) return;
    void (async () => {
      try {
        const b = await getBatch(batchId);
        setBatch(b);
        setMessages(await listBatchChatMessages(batchId));
        try {
          setAnalysis(await getLatestBatchAnalysis(batchId));
        } catch (err) {
          if (err instanceof ApiError && err.status === 404) setAnalysis(null);
          else throw err;
        }
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("errors.loadChat"));
      }
    })();
  }, [batchId, t]);

  const handleSend = async (message: string) => {
    setError(null);
    try {
      const result = await sendBatchChatMessage(batchId, message);
      setMessages((prev) => [...prev, result.user_message, result.assistant_message]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.chatFailed"));
      throw err;
    }
  };

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>{t("batch.chat.title")}</h1>
      {batch && (
        <p className="muted">
          {batch.name} ({batch.report_count} {t("batch.list.reports")}) ·{" "}
          <Link to={`/batches/${batch.id}`}>{t("batch.backToBatch")}</Link>
          {hasAnalysis && (
            <>
              {" · "}
              <Link to={`/batches/${batch.id}/analysis`}>{t("batch.details.discussAnalysis")}</Link>
            </>
          )}
        </p>
      )}

      {hasAnalysis ? (
        <p className="muted">{t("batch.chat.hintWithAnalysis")}</p>
      ) : (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <p className="muted" style={{ margin: 0 }}>
            {t("batch.chat.runAnalysisFirst")}{" "}
            <Link to={`/batches/${batchId}/analysis`}>{t("batch.analyzeAll")}</Link>
          </p>
        </div>
      )}

      {error && <div className="error">{error}</div>}
      <ChatBox
        messages={messages}
        onSend={handleSend}
        placeholder={hasAnalysis ? t("batch.analysis.chat.placeholder") : t("batch.chat.placeholder")}
        emptyHint={hasAnalysis ? t("batch.analysis.chat.emptyHint") : t("batch.chat.emptyHint")}
        suggestedPrompts={suggestedPrompts}
      />
    </div>
  );
}
