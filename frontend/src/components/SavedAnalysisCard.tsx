import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { SavedAnalysis } from "../api/savedAnalyses";

interface Props {
  item: SavedAnalysis;
  selected?: boolean;
  onSelect?: (id: number, checked: boolean) => void;
  onDelete?: (id: number) => void;
}

export default function SavedAnalysisCard({ item, selected = false, onSelect, onDelete }: Props) {
  const { t, i18n } = useTranslation();
  const locale = i18n.language === "ar" ? "ar" : "en";
  const isBatch = item.source_type === "batch";
  const dateLabel = new Date(item.created_at).toLocaleString(locale);

  return (
    <article className={`report-card saved-analysis-card${selected ? " report-card-selected" : ""}`}>
      {onSelect && (
        <label className="report-card-checkbox" title={t("savedAnalyses.selectItem")}>
          <input
            type="checkbox"
            checked={selected}
            onChange={(e) => onSelect(item.id, e.target.checked)}
            aria-label={t("savedAnalyses.selectItemNamed", { title: item.title })}
          />
        </label>
      )}

      <div
        className="saved-analysis-icon"
        style={{ background: isBatch ? "#ede9fe" : "#dbeafe", color: isBatch ? "#6d28d9" : "#2563eb" }}
        aria-hidden
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
          {isBatch ? (
            <path d="M4 7h16M4 12h16M4 17h10" strokeLinecap="round" />
          ) : (
            <path d="M7 3h7l5 5v13H7V3zm7 0v5h5M9 13h6M9 17h4" strokeLinecap="round" strokeLinejoin="round" />
          )}
        </svg>
      </div>

      <div className="report-card-body">
        <div className="report-card-title-row">
          <h3 className="report-card-title" title={item.title}>
            {item.title}
          </h3>
          <span className={`report-badge ${isBatch ? "saved-analysis-badge-batch" : "saved-analysis-badge-report"}`}>
            {isBatch ? t("savedAnalyses.typeBatch") : t("savedAnalyses.typeReport")}
          </span>
        </div>
        <div className="report-card-meta">
          <span>{item.source_name}</span>
          <span className="report-meta-dot" aria-hidden />
          <span>{item.filename}</span>
          <span className="report-meta-dot" aria-hidden />
          <span>{dateLabel}</span>
        </div>
      </div>

      <div className="report-card-actions">
        <Link
          className="report-icon-btn"
          to={`/saved-analyses/${item.id}`}
          title={t("common.view")}
          aria-label={t("common.view")}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </Link>
        {onDelete && (
          <button
            type="button"
            className="report-icon-btn report-icon-btn-danger"
            onClick={() => onDelete(item.id)}
            title={t("common.delete")}
            aria-label={t("common.delete")}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
              <path d="M3 6h18M8 6V4h8v2m-1 0v14H9V6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        )}
      </div>
    </article>
  );
}
