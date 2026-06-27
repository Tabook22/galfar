import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import { deleteBatch, getBatch, getBatchReportAnalyses, runBatchAnalysis, type BatchDetail } from "../api/batches";
import ReportCard from "../components/ReportCard";
import ConfirmDialog from "../components/ConfirmDialog";
import { useConfirmDialog } from "../hooks/useConfirmDialog";

export default function BatchDetails() {
  const { t } = useTranslation();
  const { id } = useParams();
  const batchId = Number(id);
  const navigate = useNavigate();
  const [batch, setBatch] = useState<BatchDetail | null>(null);
  const [savedAnalysisCount, setSavedAnalysisCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const confirmDialog = useConfirmDialog();

  useEffect(() => {
    if (!batchId) return;
    void (async () => {
      try {
        const b = await getBatch(batchId);
        setBatch(b);
        const reportAnalyses = await getBatchReportAnalyses(batchId);
        setSavedAnalysisCount(
          reportAnalyses.items.filter((item) => item.analysis?.status === "completed").length
        );
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("batch.errors.load"));
      }
    })();
  }, [batchId]);

  const handleAnalyze = async () => {
    if (!batch) return;
    setAnalyzing(true);
    setError(null);
    try {
      await runBatchAnalysis(batch.id, true);
      navigate(`/batches/${batch.id}/analysis`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.analysisFailed"));
    } finally {
      setAnalyzing(false);
    }
  };

  const handleDelete = () => {
    if (!batch) return;
    confirmDialog.requestConfirm(t("batch.confirm.delete"), async () => {
      try {
        await deleteBatch(batch.id);
        navigate("/batches");
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("errors.deleteFailed"));
        throw err;
      }
    });
  };

  if (!batch && !error) return <p className="muted">{t("common.loading")}</p>;
  if (error && !batch) return <div className="error">{error}</div>;
  if (!batch) return null;

  return (
    <div>
      <div className="page-actions">
        <div>
          <h1 style={{ marginTop: 0 }}>{batch.name}</h1>
          <p className="muted">
            {batch.report_count} {t("batch.list.reports")} · {t(`status.${batch.status}`, { defaultValue: batch.status })}
            {savedAnalysisCount > 0 && (
              <> · {t("batch.details.savedAnalyses", { count: savedAnalysisCount, total: batch.report_count })}</>
            )}
          </p>
        </div>
        <div className="action-buttons">
          <button className="btn" onClick={() => void handleAnalyze()} disabled={analyzing}>
            {analyzing ? t("reportDetails.analyzing") : t("batch.analyzeAll")}
          </button>
          <Link className="btn btn-secondary" to={`/batches/${batch.id}/analysis`} style={{ padding: "0.6rem 1rem" }}>
            {batch.has_analysis ? t("batch.details.discussAnalysis") : t("batch.list.bigPicture")}
          </Link>
          <button className="btn btn-danger" onClick={handleDelete}>
            {t("common.delete")}
          </button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <h2>{t("batch.details.includedReports")}</h2>
      <div className="grid">
        {batch.reports.map((report) => (
          <ReportCard key={report.id} report={report} />
        ))}
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
