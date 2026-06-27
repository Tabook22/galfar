import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import {
  deleteSavedAnalysis,
  getSavedAnalysis,
  reanalyzeSavedAnalysis,
  updateSavedAnalysis,
  type SavedAnalysisDetail,
} from "../api/savedAnalyses";
import ReanalyzeDialog from "../components/ReanalyzeDialog";
import ConfirmDialog from "../components/ConfirmDialog";
import RichTextContent from "../components/RichTextContent";
import RichTextEditor from "../components/RichTextEditor";
import { useConfirmDialog } from "../hooks/useConfirmDialog";
import { fromEditorHtml } from "../utils/richText";
import { readField, resolveSavedAnalysisDocument, toEditorDocument } from "../utils/savedAnalysisDocument";

export default function SavedAnalysisDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams();
  const savedId = Number(id);
  const navigate = useNavigate();
  const [item, setItem] = useState<SavedAnalysisDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [reanalyzeOpen, setReanalyzeOpen] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [title, setTitle] = useState("");
  const [documentHtml, setDocumentHtml] = useState("");
  const confirmDialog = useConfirmDialog();

  const sectionLabel = (key: string) => t(`reportAnalysis.sections.${key}`);

  const buildDocument = (detail: SavedAnalysisDetail) =>
    resolveSavedAnalysisDocument(detail.content, detail.source_type, (key) => sectionLabel(key));

  useEffect(() => {
    if (!savedId) return;
    void (async () => {
      try {
        const loaded = await getSavedAnalysis(savedId);
        setItem(loaded);
        setTitle(loaded.title);
        setDocumentHtml(buildDocument(loaded));
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("savedAnalyses.errors.loadOne"));
      }
    })();
  }, [savedId, t]);

  const resetForm = () => {
    if (!item) return;
    setTitle(item.title);
    setDocumentHtml(buildDocument(item));
  };

  const handleDelete = () => {
    if (!item) return;
    confirmDialog.requestConfirm(t("savedAnalyses.confirmDelete", { title: item.title }), async () => {
      try {
        await deleteSavedAnalysis(item.id);
        navigate("/saved-analyses");
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("errors.deleteFailed"));
        throw err;
      }
    });
  };

  const handleStartEdit = () => {
    resetForm();
    setDocumentHtml((prev) => toEditorDocument(prev));
    setEditing(true);
    setError(null);
    setSuccess(null);
  };

  const handleCancelEdit = () => {
    resetForm();
    setEditing(false);
    setError(null);
    setSuccess(null);
  };

  const handleReanalyze = async (criteria: string) => {
    if (!item) return;
    setReanalyzing(true);
    setError(null);
    setSuccess(null);
    try {
      const updated = await reanalyzeSavedAnalysis(item.id, criteria);
      setItem(updated);
      setTitle(updated.title);
      setDocumentHtml(buildDocument(updated));
      setSuccess(t("savedAnalyses.reanalyzeSuccess"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("savedAnalyses.errors.reanalyze"));
      throw err;
    } finally {
      setReanalyzing(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!item) return;

    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setError(t("savedAnalyses.titleRequired"));
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const updated = await updateSavedAnalysis(item.id, {
        title: trimmedTitle,
        document_html: fromEditorHtml(documentHtml),
      });
      setItem(updated);
      setTitle(updated.title);
      setDocumentHtml(buildDocument(updated));
      setEditing(false);
      setSuccess(t("savedAnalyses.editSuccess"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("savedAnalyses.errors.update"));
    } finally {
      setSaving(false);
    }
  };

  if (error && !item) return <div className="error">{error}</div>;
  if (!item) return <p className="muted">{t("common.loading")}</p>;

  const content = item.content;
  const lastEditedAt =
    typeof content.last_edited_at === "string" ? content.last_edited_at : null;
  const lastReanalyzedAt =
    typeof content.last_reanalyzed_at === "string" ? content.last_reanalyzed_at : null;
  const lastReanalyzeCriteria =
    typeof content.last_reanalyze_criteria === "string" ? content.last_reanalyze_criteria : null;

  const reportAnalyses = Array.isArray(content.report_analyses)
    ? (content.report_analyses as Record<string, unknown>[])
    : [];

  const viewDocument = buildDocument(item);

  return (
    <div>
      <div className="page-actions">
        <div>
          {editing ? (
            <label className="edit-title-field">
              <span>{t("savedAnalyses.titleLabel")}</span>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder={t("savedAnalyses.titlePlaceholder")}
                disabled={saving}
              />
            </label>
          ) : (
            <h1 style={{ marginTop: 0 }}>{item.title}</h1>
          )}
          <p className="muted">
            {item.source_name} · {item.filename} ·{" "}
            <Link to="/saved-analyses">{t("savedAnalyses.backToList")}</Link>
          </p>
        </div>
        <div className="action-buttons">
          {!editing && (
            <>
              <button className="btn" onClick={() => setReanalyzeOpen(true)} disabled={reanalyzing}>
                {reanalyzing ? t("savedAnalyses.reanalyzing") : t("savedAnalyses.reanalyze")}
              </button>
              <button className="btn btn-secondary" onClick={handleStartEdit}>
                {t("common.edit")}
              </button>
            </>
          )}
          <button className="btn btn-danger" onClick={handleDelete} disabled={editing || reanalyzing}>
            {t("common.delete")}
          </button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      {editing ? (
        <form className="card analysis-edit-form" onSubmit={(e) => void handleSubmit(e)}>
          <p className="muted" style={{ marginTop: 0 }}>
            {t("savedAnalyses.editHint")}
          </p>

          <div className="edit-field analysis-document-editor">
            <span>{t("savedAnalyses.documentLabel")}</span>
            <RichTextEditor
              value={documentHtml}
              onChange={setDocumentHtml}
              disabled={saving}
              minHeight="480px"
              ariaLabel={t("savedAnalyses.documentLabel")}
            />
          </div>

          <div className="action-buttons">
            <button type="button" className="btn btn-secondary" onClick={handleCancelEdit} disabled={saving}>
              {t("savedAnalyses.cancel")}
            </button>
            <button type="submit" className="btn" disabled={saving || !title.trim()}>
              {saving ? t("savedAnalyses.saving") : t("common.save")}
            </button>
          </div>
        </form>
      ) : (
        <div className="card analysis-document-view">
          <p className="muted" style={{ marginTop: 0 }}>
            {item.source_type === "batch" ? t("savedAnalyses.typeBatch") : t("savedAnalyses.typeReport")} ·{" "}
            {new Date(item.created_at).toLocaleString()}
            {lastEditedAt && (
              <>
                {" "}
                · {t("savedAnalyses.lastEdited")} {new Date(lastEditedAt).toLocaleString()}
              </>
            )}
            {lastReanalyzedAt && (
              <>
                {" "}
                · {t("savedAnalyses.lastReanalyzed")} {new Date(lastReanalyzedAt).toLocaleString()}
              </>
            )}
          </p>
          {lastReanalyzeCriteria && (
            <p className="muted reanalyze-criteria-note">
              <strong>{t("savedAnalyses.lastReanalyzeFocus")}:</strong> {lastReanalyzeCriteria}
            </p>
          )}
          <RichTextContent value={viewDocument} />
        </div>
      )}

      {!editing && reportAnalyses.length > 0 && (
        <>
          <h2>{t("batch.analysis.savedReportsTitle")}</h2>
          <div className="grid">
            {reportAnalyses.map((ra, index) => (
              <div key={index} className="card">
                <h3 style={{ marginTop: 0 }}>
                  {typeof ra.original_filename === "string" ? ra.original_filename : t("savedAnalyses.report")}
                </h3>
                <div>
                  {readField(ra, "summary") ? (
                    <RichTextContent value={readField(ra, "summary")} />
                  ) : (
                    t("common.notAvailable")
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <ReanalyzeDialog
        open={reanalyzeOpen}
        saving={reanalyzing}
        onClose={() => setReanalyzeOpen(false)}
        onSubmit={handleReanalyze}
      />

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
