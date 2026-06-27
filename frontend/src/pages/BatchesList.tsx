import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import { deleteBatch, listBatches, type ReportBatch } from "../api/batches";
import ConfirmDialog from "../components/ConfirmDialog";
import { useConfirmDialog } from "../hooks/useConfirmDialog";

export default function BatchesList() {
  const { t } = useTranslation();
  const [batches, setBatches] = useState<ReportBatch[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const confirmDialog = useConfirmDialog();

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setBatches(await listBatches());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("batch.errors.load"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const handleDelete = (id: number) => {
    confirmDialog.requestConfirm(t("batch.confirm.delete"), async () => {
      try {
        await deleteBatch(id);
        setBatches((prev) => prev.filter((b) => b.id !== id));
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("errors.deleteFailed"));
        throw err;
      }
    });
  };

  const statusLabel = (status: string) => t(`status.${status}`, { defaultValue: status });

  return (
    <div>
      <div className="page-actions">
        <h1 style={{ marginTop: 0 }}>{t("batch.list.title")}</h1>
        <Link to="/batches/upload" className="btn">
          {t("batch.upload.title")}
        </Link>
      </div>
      <p className="muted">{t("batch.list.subtitle")}</p>
      {error && <div className="error">{error}</div>}
      {loading && <p className="muted">{t("common.loading")}</p>}
      {!loading && batches.length === 0 && (
        <div className="card">
          <p className="muted">{t("batch.list.empty")}</p>
        </div>
      )}
      <div className="grid">
        {batches.map((batch) => (
          <div key={batch.id} className="card">
            <div className="report-card-inner">
              <div>
                <h3 style={{ margin: "0 0 0.35rem" }}>{batch.name}</h3>
                <p className="muted" style={{ margin: 0 }}>
                  {batch.report_count} {t("batch.list.reports")} · {statusLabel(batch.status)}
                </p>
                <p className="muted" style={{ margin: "0.35rem 0 0", fontSize: "0.85rem" }}>
                  {new Date(batch.created_at).toLocaleString()}
                </p>
              </div>
              <div className="report-card-actions">
                <Link to={`/batches/${batch.id}`}>{t("common.view")}</Link>
                <Link to={`/batches/${batch.id}/analysis`}>{t("batch.list.bigPicture")}</Link>
                <Link to={`/batches/${batch.id}/chat`}>{t("common.chat")}</Link>
                <button className="btn btn-danger" onClick={() => handleDelete(batch.id)}>
                  {t("common.delete")}
                </button>
              </div>
            </div>
          </div>
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
