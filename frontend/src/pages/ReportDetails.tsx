import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import { deleteReport, getReport, getReportDownloadUrl, runAnalysis, type ReportDetail } from "../api/reports";
import ConfirmDialog from "../components/ConfirmDialog";
import { useConfirmDialog } from "../hooks/useConfirmDialog";

export default function ReportDetails() {
  const { t } = useTranslation();
  const { id } = useParams();
  const reportId = Number(id);
  const navigate = useNavigate();
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const confirmDialog = useConfirmDialog();

  useEffect(() => {
    if (!reportId) return;
    void (async () => {
      try {
        setReport(await getReport(reportId));
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("errors.loadReport"));
      }
    })();
  }, [reportId]);

  const handleAnalyze = async () => {
    if (!report) return;
    setAnalyzing(true);
    setError(null);
    try {
      await runAnalysis(report.id, true);
      navigate(`/reports/${report.id}/analysis`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.analysisFailed"));
    } finally {
      setAnalyzing(false);
    }
  };

  const handleDelete = () => {
    if (!report) return;
    confirmDialog.requestConfirm(t("confirm.deleteReport"), async () => {
      try {
        await deleteReport(report.id);
        navigate("/reports");
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("errors.deleteFailed"));
        throw err;
      }
    });
  };

  const statusLabel = (status: string) => {
    const key = `status.${status}`;
    return t(key, { defaultValue: status });
  };

  if (!report && !error) return <p className="muted">{t("reportDetails.loading")}</p>;
  if (error && !report) return <div className="error">{error}</div>;
  if (!report) return null;

  return (
    <div>
      <div className="page-actions">
        <div>
          <h1 style={{ marginTop: 0 }}>{report.original_filename}</h1>
          <p className="muted">
            {t("common.status")}: {statusLabel(report.status)} · {t("common.type")}: {report.file_type} ·{" "}
            {t("common.size")}: {report.file_size} {t("common.bytes")}
          </p>
        </div>
        <div className="action-buttons">
          <a
            className="btn btn-secondary"
            href={getReportDownloadUrl(report.id)}
            download={report.original_filename}
            style={{ padding: "0.6rem 1rem", textDecoration: "none" }}
          >
            {t("common.download")}
          </a>
          <button className="btn" onClick={() => void handleAnalyze()} disabled={analyzing}>
            {analyzing
              ? t("reportDetails.analyzing")
              : report.has_analysis
                ? t("reportAnalysis.rerunAnalysis")
                : t("reportDetails.runAnalysis")}
          </button>
          {report.has_analysis && (
            <Link className="btn btn-secondary" to={`/reports/${report.id}/analysis`} style={{ padding: "0.6rem 1rem" }}>
              {t("reportDetails.discussAnalysis")}
            </Link>
          )}
          {!report.has_analysis && (
            <Link className="btn btn-secondary" to={`/reports/${report.id}/chat`} style={{ padding: "0.6rem 1rem" }}>
              {t("common.chat")}
            </Link>
          )}
          <button className="btn btn-danger" onClick={handleDelete}>
            {t("common.delete")}
          </button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="grid" style={{ marginTop: "1rem" }}>
        <div className="card">
          <h2 className="section-title">{t("reportDetails.metadata")}</h2>
          <p>
            <strong>{t("common.uploaded")}:</strong> {new Date(report.created_at).toLocaleString()}
          </p>
          <p>
            <strong>{t("reportDetails.analyses")}:</strong> {report.analysis_count}
          </p>
          <p>
            <strong>{t("reportDetails.chatMessages")}:</strong> {report.chat_message_count}
          </p>
          {report.has_analysis && report.latest_analysis_id && (
            <p>
              <Link to={`/reports/${report.id}/analysis`}>{t("reportDetails.viewLatestAnalysis")}</Link>
              {" · "}
              <Link to={`/reports/${report.id}/analysis`}>{t("reportDetails.discussAnalysis")}</Link>
            </p>
          )}
        </div>
        <div className="card">
          <h2 className="section-title">{t("reportDetails.extractedPreview")}</h2>
          <p style={{ whiteSpace: "pre-wrap" }}>
            {report.extracted_text_preview ?? t("reportDetails.noTextExtracted")}
          </p>
        </div>
      </div>

      <ConfirmDialog
        open={confirmDialog.open}
        message={confirmDialog.message}
        loading={confirmDialog.loading}
        onConfirm={() => void confirmDialog.confirm()}
        onCancel={confirmDialog.cancel}
      />
    </div>
  );
}
