import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import {
  deleteSavedAnalysis,
  deleteSavedAnalyses,
  listSavedAnalyses,
  type SavedAnalysis,
} from "../api/savedAnalyses";
import SavedAnalysisCard from "../components/SavedAnalysisCard";
import ConfirmDialog from "../components/ConfirmDialog";
import { useConfirmDialog } from "../hooks/useConfirmDialog";

export default function SavedAnalysesList() {
  const { t } = useTranslation();
  const [items, setItems] = useState<SavedAnalysis[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const confirmDialog = useConfirmDialog();

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await listSavedAnalyses();
      setItems(list);
      setSelectedIds((prev) => {
        const visible = new Set(list.map((x) => x.id));
        return new Set([...prev].filter((id) => visible.has(id)));
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("savedAnalyses.errors.load"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const allSelected = items.length > 0 && items.every((item) => selectedIds.has(item.id));
  const someSelected = selectedIds.size > 0;
  const selectedCount = selectedIds.size;

  const toggleSelectAll = (checked: boolean) => {
    setSelectedIds(checked ? new Set(items.map((item) => item.id)) : new Set());
  };

  const toggleSelect = (id: number, checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const handleDelete = (id: number) => {
    const item = items.find((x) => x.id === id);
    if (!item) return;
    confirmDialog.requestConfirm(t("savedAnalyses.confirmDelete", { title: item.title }), async () => {
      try {
        await deleteSavedAnalysis(id);
        setItems((prev) => prev.filter((x) => x.id !== id));
        setSelectedIds((prev) => {
          const next = new Set(prev);
          next.delete(id);
          return next;
        });
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("errors.deleteFailed"));
        throw err;
      }
    });
  };

  const handleBulkDelete = (ids: number[]) => {
    if (ids.length === 0) return;
    const message =
      ids.length === 1
        ? t("savedAnalyses.confirmDelete", { title: items.find((x) => x.id === ids[0])?.title ?? "" })
        : t("savedAnalyses.confirmDeleteBulk", { count: ids.length });

    confirmDialog.requestConfirm(message, async () => {
      setDeleting(true);
      setError(null);
      try {
        const result = await deleteSavedAnalyses(ids);
        const removed = new Set(ids);
        setItems((prev) => prev.filter((x) => !removed.has(x.id)));
        setSelectedIds((prev) => {
          const next = new Set(prev);
          ids.forEach((id) => next.delete(id));
          return next;
        });
        if (result.deleted_count === 0) {
          setError(t("errors.deleteFailed"));
        }
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("errors.deleteFailed"));
        throw err;
      } finally {
        setDeleting(false);
      }
    });
  };

  return (
    <div className="reports-page">
      <div className="reports-page-header">
        <div>
          <h1 style={{ marginTop: 0 }}>{t("savedAnalyses.listTitle")}</h1>
          <p className="muted">{t("savedAnalyses.listSubtitle")}</p>
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <p className="muted">{t("common.loading")}</p>}

      {!loading && items.length === 0 && (
        <div className="card reports-empty">
          <p className="muted">{t("savedAnalyses.empty")}</p>
        </div>
      )}

      {!loading && items.length > 0 && (
        <>
          <p className="reports-count muted">{t("savedAnalyses.showingCount", { count: items.length })}</p>

          <div className="reports-list-header">
            <label className="reports-select-all">
              <input
                type="checkbox"
                checked={allSelected}
                ref={(el) => {
                  if (el) el.indeterminate = someSelected && !allSelected;
                }}
                onChange={(e) => toggleSelectAll(e.target.checked)}
                aria-label={t("savedAnalyses.selectAll")}
              />
              <span>{t("savedAnalyses.selectAll")}</span>
            </label>
            {someSelected && (
              <div className="reports-bulk-actions">
                <span className="reports-selected-count">
                  {t("savedAnalyses.selectedCount", { count: selectedCount })}
                </span>
                <button
                  type="button"
                  className="btn btn-danger reports-bulk-delete"
                  disabled={deleting}
                  onClick={() => handleBulkDelete([...selectedIds])}
                >
                  {deleting ? t("savedAnalyses.deleting") : t("savedAnalyses.deleteSelected")}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={deleting}
                  onClick={() => setSelectedIds(new Set())}
                >
                  {t("savedAnalyses.clearSelection")}
                </button>
              </div>
            )}
          </div>

          <div className="reports-list">
            {items.map((item) => (
              <SavedAnalysisCard
                key={item.id}
                item={item}
                selected={selectedIds.has(item.id)}
                onSelect={toggleSelect}
                onDelete={handleDelete}
              />
            ))}
          </div>
        </>
      )}

      <ConfirmDialog
        open={confirmDialog.open}
        message={confirmDialog.message}
        loading={confirmDialog.loading || deleting}
        onConfirm={() => void confirmDialog.confirm()}
        onCancel={confirmDialog.cancel}
      />
    </div>
  );
}
