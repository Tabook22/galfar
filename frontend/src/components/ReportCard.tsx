import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getReportDownloadUrl, type Report } from "../api/reports";
import ReportFileIcon, { categoryLabel } from "./ReportFileIcon";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface Props {
  report: Report;
  selected?: boolean;
  onSelect?: (id: number, checked: boolean) => void;
  onDelete?: (id: number) => void;
}

export default function ReportCard({ report, selected = false, onSelect, onDelete }: Props) {
  const { t, i18n } = useTranslation();
  const locale = i18n.language === "ar" ? "ar" : "en";
  const statusLabel = t(`status.${report.status}`, { defaultValue: report.status });
  const analyzed = report.status === "analyzed" || report.has_analysis;
  const dateLabel = new Date(report.created_at).toLocaleDateString(locale, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <article className={`report-card${selected ? " report-card-selected" : ""}`}>
      {onSelect && (
        <label className="report-card-checkbox" title={t("reports.selectReport")}>
          <input
            type="checkbox"
            checked={selected}
            onChange={(e) => onSelect(report.id, e.target.checked)}
            aria-label={t("reports.selectReportNamed", { name: report.original_filename })}
          />
        </label>
      )}

      <ReportFileIcon fileType={report.file_type} size={40} showLabel={false} />

      <div className="report-card-body">
        <div className="report-card-title-row">
          <h3 className="report-card-title" title={report.original_filename}>
            {report.original_filename}
          </h3>
          <span className={`report-badge ${analyzed ? "report-badge-success" : "report-badge-muted"}`}>
            {analyzed ? t("reports.badgeAnalyzed") : statusLabel}
          </span>
        </div>
        <div className="report-card-meta">
          <span>{categoryLabel(report.file_type)}</span>
          <span className="report-meta-dot" aria-hidden />
          <span>{formatBytes(report.file_size)}</span>
          <span className="report-meta-dot" aria-hidden />
          <span>{dateLabel}</span>
        </div>
      </div>

      <div className="report-card-actions">
        <Link className="report-icon-btn" to={`/reports/${report.id}`} title={t("common.view")} aria-label={t("common.view")}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </Link>
        <Link
          className="report-icon-btn"
          to={`/reports/${report.id}/analysis`}
          title={report.has_analysis ? t("reportDetails.discussAnalysis") : t("common.analysis")}
          aria-label={t("common.analysis")}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <path d="M3 3v18h18M7 16l4-8 4 5 5-9" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </Link>
        <Link
          className="report-icon-btn"
          to={`/reports/${report.id}/chat`}
          title={t("common.chat")}
          aria-label={t("common.chat")}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </Link>
        <a
          className="report-icon-btn"
          href={getReportDownloadUrl(report.id)}
          download={report.original_filename}
          title={t("common.download")}
          aria-label={t("common.download")}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <path d="M12 3v12M7 10l5 5 5-5M5 21h14" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </a>
        {onDelete && (
          <button
            type="button"
            className="report-icon-btn report-icon-btn-danger"
            onClick={() => onDelete(report.id)}
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
