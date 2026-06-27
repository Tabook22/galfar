import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import {
  getLatestAnalysis,
  getReport,
  listChatMessages,
  runAnalysis,
  sendChatMessage,
  type Analysis,
  type ChatMessage,
  type ReportDetail,
} from "../api/reports";
import ChatBox from "../components/ChatBox";
import SaveAnalysisDialog from "../components/SaveAnalysisDialog";
import { saveReportAnalysis } from "../api/savedAnalyses";

function AnalysisSection({ title, value }: { title: string; value: string | null }) {
  const { t } = useTranslation();
  return (
    <div className="analysis-section">
      <h3>{title}</h3>
      <p>{value ?? t("common.notAvailable")}</p>
    </div>
  );
}

export default function ReportAnalysis() {
  const { t } = useTranslation();
  const { id } = useParams();
  const reportId = Number(id);
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatError, setChatError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [saveOpen, setSaveOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  const suggestedPrompts = useMemo(
    () => [
      t("reportAnalysis.chat.prompts.summary"),
      t("reportAnalysis.chat.prompts.revenue"),
      t("reportAnalysis.chat.prompts.risks"),
      t("reportAnalysis.chat.prompts.recommendations"),
    ],
    [t]
  );

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await getReport(reportId);
      setReport(r);
      try {
        setAnalysis(await getLatestAnalysis(reportId));
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setAnalysis(null);
        } else {
          throw err;
        }
      }
      if (r.has_analysis) {
        try {
          setMessages(await listChatMessages(reportId));
        } catch {
          setMessages([]);
        }
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.loadAnalysis"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (reportId) void load();
  }, [reportId]);

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    try {
      const result = await runAnalysis(reportId, true);
      setAnalysis(result);
      setReport(await getReport(reportId));
      try {
        setMessages(await listChatMessages(reportId));
      } catch {
        setMessages([]);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.analysisFailed"));
    } finally {
      setRunning(false);
    }
  };

  const handleSend = async (message: string) => {
    setChatError(null);
    try {
      const result = await sendChatMessage(reportId, message);
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
      const saved = await saveReportAnalysis(reportId, title, analysis.id);
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

  return (
    <div>
      <div className="page-actions">
        <div>
          <h1 style={{ marginTop: 0 }}>{t("reportAnalysis.title")}</h1>
          {report && (
            <p className="muted">
              {report.original_filename} · <Link to={`/reports/${report.id}`}>{t("common.backToReport")}</Link>
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
            {running
              ? t("reportAnalysis.running")
              : analysis
                ? t("reportAnalysis.rerunAnalysis")
                : t("reportAnalysis.runAnalysis")}
          </button>
        </div>
      </div>

      {saveSuccess && <div className="success">{saveSuccess}</div>}

      {error && <div className="error">{error}</div>}

      {!analysis && !error && (
        <div className="card">
          <p className="muted">{t("reportAnalysis.empty")}</p>
        </div>
      )}

      {analysis && (
        <div className="analysis-with-chat">
          <div className="card">
            <p className="muted" style={{ marginTop: 0 }}>
              {t("common.status")}: {analysis.status} · {new Date(analysis.created_at).toLocaleString()}
            </p>
            {analysis.error_message && <div className="error">{analysis.error_message}</div>}
            {sections.map(({ key, value }) => (
              <AnalysisSection
                key={key}
                title={t(`reportAnalysis.sections.${key}`)}
                value={value ?? null}
              />
            ))}
          </div>

          <div className="analysis-chat-panel">
            <h2 className="section-title">{t("reportAnalysis.chat.title")}</h2>
            <p className="muted">{t("reportAnalysis.chat.hint")}</p>
            {chatError && <div className="error">{chatError}</div>}
            <ChatBox
              messages={messages}
              onSend={handleSend}
              placeholder={t("reportAnalysis.chat.placeholder")}
              emptyHint={t("reportAnalysis.chat.emptyHint")}
              suggestedPrompts={suggestedPrompts}
            />
          </div>
        </div>
      )}

      <SaveAnalysisDialog
        open={saveOpen}
        defaultTitle={report?.original_filename?.replace(/\.[^.]+$/, "") ?? ""}
        saving={saving}
        onClose={() => setSaveOpen(false)}
        onSave={handleSave}
      />
    </div>
  );
}
