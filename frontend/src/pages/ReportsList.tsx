import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import {
  deleteReport,
  deleteReports,
  listReportCategories,
  listReports,
  type Report,
} from "../api/reports";
import ReportCard from "../components/ReportCard";
import ConfirmDialog from "../components/ConfirmDialog";
import { useConfirmDialog } from "../hooks/useConfirmDialog";

type SortBy = "date" | "name" | "category";
type SortOrder = "asc" | "desc";

export default function ReportsList() {
  const { t } = useTranslation();
  const [reports, setReports] = useState<Report[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [sortBy, setSortBy] = useState<SortBy>("date");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const confirmDialog = useConfirmDialog();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [items, cats] = await Promise.all([
        listReports({
          search: search.trim() || undefined,
          category: category === "all" ? undefined : category,
          sort_by: sortBy,
          sort_order: sortOrder,
        }),
        listReportCategories(),
      ]);
      setReports(items);
      setCategories(cats);
      setSelectedIds((prev) => {
        const visible = new Set(items.map((r) => r.id));
        return new Set([...prev].filter((id) => visible.has(id)));
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.loadReports"));
    } finally {
      setLoading(false);
    }
  }, [search, category, sortBy, sortOrder, t]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), search ? 300 : 0);
    return () => window.clearTimeout(timer);
  }, [load, search]);

  const allSelected = reports.length > 0 && reports.every((r) => selectedIds.has(r.id));
  const someSelected = selectedIds.size > 0;
  const selectedCount = selectedIds.size;

  const toggleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(reports.map((r) => r.id)));
    } else {
      setSelectedIds(new Set());
    }
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
    confirmDialog.requestConfirm(t("confirm.deleteReportFull"), async () => {
      try {
        await deleteReport(id);
        setReports((prev) => prev.filter((r) => r.id !== id));
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
        ? t("confirm.deleteReportFull")
        : t("confirm.deleteReportsBulk", { count: ids.length });

    confirmDialog.requestConfirm(message, async () => {
      setDeleting(true);
      setError(null);
      try {
        const result = await deleteReports(ids);
        const removed = new Set(ids);
        setReports((prev) => prev.filter((r) => !removed.has(r.id)));
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

  const toggleSortOrder = () => setSortOrder((o) => (o === "asc" ? "desc" : "asc"));

  return (
    <div className="reports-page">
      <div className="reports-page-header">
        <div>
          <h1 style={{ marginTop: 0 }}>{t("reports.title")}</h1>
          <p className="muted">{t("reports.subtitle")}</p>
        </div>
        <Link to="/upload" className="btn">
          {t("dashboard.uploadReport")}
        </Link>
      </div>

      <div className="reports-toolbar card">
        <div className="reports-search-wrap">
          <svg className="reports-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <circle cx="11" cy="11" r="7" />
            <path d="M20 20l-3-3" strokeLinecap="round" />
          </svg>
          <input
            type="search"
            className="reports-search-input"
            placeholder={t("reports.searchPlaceholder")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select
          className="reports-select"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          aria-label={t("reports.filterCategory")}
        >
          <option value="all">{t("reports.allCategories")}</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat.toUpperCase()}
            </option>
          ))}
        </select>

        <select
          className="reports-select"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortBy)}
          aria-label={t("reports.sortBy")}
        >
          <option value="date">{t("reports.sortDate")}</option>
          <option value="name">{t("reports.sortName")}</option>
          <option value="category">{t("reports.sortCategory")}</option>
        </select>

        <button type="button" className="btn btn-secondary reports-sort-toggle" onClick={toggleSortOrder}>
          {sortOrder === "asc" ? t("reports.sortAsc") : t("reports.sortDesc")}
        </button>
      </div>

      {!loading && (
        <p className="reports-count muted">
          {t("reports.showingCount", { count: reports.length })}
        </p>
      )}

      {error && <div className="error">{error}</div>}
      {loading && <p className="muted">{t("common.loading")}</p>}

      {!loading && reports.length === 0 && (
        <div className="card reports-empty">
          <div className="reports-empty-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
              <path d="M4 4h16v16H4V4zm4 4h8m-8 4h8m-8 4h5" strokeLinecap="round" />
            </svg>
          </div>
          <h3>{t("reports.emptyTitle")}</h3>
          <p className="muted">{search || category !== "all" ? t("reports.noResults") : t("reports.empty")}</p>
          {!search && category === "all" && (
            <Link to="/upload" className="btn" style={{ marginTop: "0.5rem" }}>
              {t("dashboard.uploadReport")}
            </Link>
          )}
        </div>
      )}

      {!loading && reports.length > 0 && (
        <div className="reports-list-header">
          <label className="reports-select-all">
            <input
              type="checkbox"
              checked={allSelected}
              ref={(el) => {
                if (el) el.indeterminate = someSelected && !allSelected;
              }}
              onChange={(e) => toggleSelectAll(e.target.checked)}
              aria-label={t("reports.selectAll")}
            />
            <span>{t("reports.selectAll")}</span>
          </label>
          {someSelected && (
            <div className="reports-bulk-actions">
              <span className="reports-selected-count">
                {t("reports.selectedCount", { count: selectedCount })}
              </span>
              <button
                type="button"
                className="btn btn-danger reports-bulk-delete"
                disabled={deleting}
                onClick={() => handleBulkDelete([...selectedIds])}
              >
                {deleting ? t("reports.deleting") : t("reports.deleteSelected")}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={deleting}
                onClick={() => setSelectedIds(new Set())}
              >
                {t("reports.clearSelection")}
              </button>
            </div>
          )}
        </div>
      )}

      <div className="reports-list">
        {reports.map((report) => (
          <ReportCard
            key={report.id}
            report={report}
            selected={selectedIds.has(report.id)}
            onSelect={toggleSelect}
            onDelete={handleDelete}
          />
        ))}
      </div>

      <ConfirmDialog
        open={confirmDialog.open}
        message={confirmDialog.message}
        title={confirmDialog.title}
        loading={confirmDialog.loading || deleting}
        onConfirm={() => void confirmDialog.confirm().catch((err) => {
          if (!(err instanceof ApiError)) {
            setError(t("errors.deleteFailed"));
          }
        })}
        onCancel={confirmDialog.cancel}
      />
    </div>
  );
}
