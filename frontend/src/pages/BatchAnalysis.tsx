import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import {
  getBatch,
  getBatchReportAnalyses,
  getLatestBatchAnalysis,
  listBatchChatMessages,
  runBatchAnalysis,
  sendBatchChatMessage,
  type BatchAnalysis,
  type BatchChatMessage,
  type BatchDetail,
  type BatchReportAnalysisItem,
} from "../api/batches";
import ChatBox from "../components/ChatBox";
import SaveAnalysisDialog from "../components/SaveAnalysisDialog";
import { saveBatchAnalysis } from "../api/savedAnalyses";

function Section({ title, value }: { title: string; value: string | null }) {
  const { t } = useTranslation();
  return (
    <div className="analysis-section">
      <h3>{title}</h3>
      <p>{value ?? t("common.notAvailable")}</p>
    </div>
  );
}

function ReportAnalysisCard({ item }: { item: BatchReportAnalysisItem }) {
  const { t } = useTranslation();
  const analysis = item.analysis;

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>{item.original_filename}</h3>
      {!analysis && <p className="muted">{t("batch.analysis.noReportAnalysis")}</p>}
      {analysis && (
        <>
          <p className="muted" style={{ marginTop: 0 }}>
            {t("common.status")}: {analysis.status} · {new Date(analysis.created_at).toLocaleString()}
          </p>
          {analysis.summary && <p>{analysis.summary}</p>}
          <Link to={`/reports/${item.report_id}/analysis`}>{t("batch.analysis.viewReportAnalysis")}</Link>
        </>
      )}
    </div>
  );
}

export default function BatchAnalysisPage() {
  const { t } = useTranslation();
  const { id } = useParams();
  const batchId = Number(id);
  const [batch, setBatch] = useState<BatchDetail | null>(null);
  const [analysis, setAnalysis] = useState<BatchAnalysis | null>(null);
  const [reportAnalyses, setReportAnalyses] = useState<BatchReportAnalysisItem[]>([]);
  const [messages, setMessages] = useState<BatchChatMessage[]>([]);
  const [chatError, setChatError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [saveOpen, setSaveOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  const suggestedPrompts = useMemo(
    () => [
      t("batch.analysis.chat.prompts.summary"),
      t("batch.analysis.chat.prompts.revenue"),
      t("batch.analysis.chat.prompts.compare"),
      t("batch.analysis.chat.prompts.risks"),
    ],
    [t]
  );

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const b = await getBatch(batchId);
      setBatch(b);
      setReportAnalyses((await getBatchReportAnalyses(batchId)).items);
      try {
        setAnalysis(await getLatestBatchAnalysis(batchId));
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) setAnalysis(null);
        else throw err;
      }
      try {
        setMessages(await listBatchChatMessages(batchId));
      } catch {
        setMessages([]);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.loadAnalysis"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (batchId) void load();
  }, [batchId]);

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    try {
      setAnalysis(await runBatchAnalysis(batchId, true));
      setBatch(await getBatch(batchId));
      setReportAnalyses((await getBatchReportAnalyses(batchId)).items);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.analysisFailed"));
    } finally {
      setRunning(false);
    }
  };

  const handleSend = async (message: string) => {
    setChatError(null);
    try {
      const result = await sendBatchChatMessage(batchId, message);
      setMessages((prev) => [...prev, result.user_message, result.assistant_message]);
    } catch (err) {
      setChatError(err instanceof ApiError ? err.message : t("errors.chatFailed"));
      throw err;
    }
  };

  const handleSave = async (title: string) => {
    if (!analysis) return;
    setSaving(true);
    setError(null);
    setSaveSuccess(null);
    try {
      const saved = await saveBatchAnalysis(batchId, title, analysis.id);
      setSaveSuccess(t("savedAnalyses.saveSuccess", { title: saved.title }));
      setSaveOpen(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("savedAnalyses.errors.save"));
      throw err;
    } finally {
      setSaving(false);
    }
  };

  const sections = [
    { key: "summary", value: analysis?.summary },
    { key: "revenue", value: analysis?.revenue },
    { key: "expenses", value: analysis?.expenses },
    { key: "profitLoss", value: analysis?.profit_loss },
    { key: "cashFlow", value: analysis?.cash_flow },
    { key: "assets", value: analysis?.assets },
    { key: "liabilities", value: analysis?.liabilities },
    { key: "risks", value: analysis?.risks },
    { key: "strengths", value: analysis?.strengths },
    { key: "weaknesses", value: analysis?.weaknesses },
    { key: "recommendations", value: analysis?.recommendations },
  ] as const;

  if (loading) return <p className="muted">{t("reportAnalysis.loading")}</p>;

  const savedCount = reportAnalyses.filter((item) => item.analysis?.status === "completed").length;

  return (
    <div>
      <div className="page-actions">
        <div>
          <h1 style={{ marginTop: 0 }}>{t("batch.analysis.title")}</h1>
          {batch && (
            <p className="muted">
              {batch.name} · {analysis?.report_count ?? batch.report_count} {t("batch.list.reports")} ·{" "}
              {t("batch.analysis.savedCount", { count: savedCount, total: batch.report_count })} ·{" "}
              <Link to={`/batches/${batch.id}`}>{t("batch.backToBatch")}</Link>
            </p>
          )}
        </div>
        <div className="action-buttons">
          {analysis?.status === "completed" && (
            <button className="btn btn-secondary" onClick={() => setSaveOpen(true)} disabled={running || saving}>
              {t("savedAnalyses.saveButton")}
            </button>
          )}
          <button className="btn" onClick={() => void handleRun()} disabled={running}>
            {running ? t("reportAnalysis.running") : analysis ? t("batch.analysis.rerun") : t("batch.analyzeAll")}
          </button>
        </div>
      </div>

      {saveSuccess && <div className="success">{saveSuccess}</div>}

      {error && <div className="error">{error}</div>}

      {!analysis && !error && (
        <div className="card">
          <p className="muted">{t("batch.analysis.empty")}</p>
        </div>
      )}

      {analysis && (
        <div className="analysis-with-chat">
          <div className="card">
            <p className="muted" style={{ marginTop: 0 }}>
              {t("batch.analysis.bigPicture")} · {new Date(analysis.created_at).toLocaleString()}
            </p>
            {analysis.error_message && <div className="error">{analysis.error_message}</div>}
            {sections.map(({ key, value }) => (
              <Section key={key} title={t(`reportAnalysis.sections.${key}`)} value={value ?? null} />
            ))}
          </div>

          <div className="analysis-chat-panel">
            <h2 className="section-title">{t("batch.analysis.chat.title")}</h2>
            <p className="muted">{t("batch.analysis.chat.hint")}</p>
            {chatError && <div className="error">{chatError}</div>}
            <ChatBox
              messages={messages}
              onSend={handleSend}
              placeholder={t("batch.analysis.chat.placeholder")}
              emptyHint={t("batch.analysis.chat.emptyHint")}
              suggestedPrompts={suggestedPrompts}
            />
          </div>
        </div>
      )}

      {reportAnalyses.length > 0 && (
        <>
          <h2>{t("batch.analysis.savedReportsTitle")}</h2>
          <p className="muted">{t("batch.analysis.savedReportsHint")}</p>
          <div className="grid">
            {reportAnalyses.map((item) => (
              <ReportAnalysisCard key={item.report_id} item={item} />
            ))}
          </div>
        </>
      )}

      <SaveAnalysisDialog
        open={saveOpen}
        defaultTitle={batch?.name ?? ""}
        saving={saving}
        onClose={() => setSaveOpen(false)}
        onSave={handleSave}
      />
    </div>
  );
}
