import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { hasCompanyProfile, pickLocalized } from "../api/settings";
import { ApiError } from "../api/client";
import { getDashboardStats, listReports, type DashboardStats, type Report } from "../api/reports";
import CompanyProfile from "../components/CompanyProfile";
import ReportCard from "../components/ReportCard";
import { useCompanyBranding, useCompanySettings } from "../context/CompanySettingsContext";

export default function Dashboard() {
  const { t, i18n } = useTranslation();
  const branding = useCompanyBranding();
  const { settings } = useCompanySettings();
  const lang = i18n.language === "ar" ? "ar" : "en";
  const pageTitle = pickLocalized(branding.page_title, lang);
  const tagline = pickLocalized(branding.tagline, lang);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [s, r] = await Promise.all([getDashboardStats(), listReports()]);
        setStats(s);
        setReports(r.slice(0, 5));
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("errors.loadDashboard"));
      }
    })();
  }, [t]);

  const showProfile = hasCompanyProfile(settings) || settings.logo_url;

  return (
    <div>
      <div className="page-actions no-print">
        <div>
          <h1 style={{ marginTop: 0 }}>{pageTitle}</h1>
          {tagline ? <p className="muted">{tagline}</p> : <p className="muted">{t("dashboard.subtitle")}</p>}
        </div>
        <div className="action-buttons">
          {showProfile && (
            <button type="button" className="btn btn-secondary" onClick={() => window.print()}>
              {t("settings.printProfile")}
            </button>
          )}
          <Link to="/settings" className="btn btn-secondary" style={{ padding: "0.6rem 1rem", textDecoration: "none" }}>
            {t("nav.settings")}
          </Link>
        </div>
      </div>

      <div className="card company-profile-preview dashboard-profile no-print">
        <CompanyProfile settings={settings} showEmptyHint />
        {!showProfile && (
          <p className="muted" style={{ marginBottom: 0 }}>
            <Link to="/settings">{t("settings.setupLink")}</Link>
          </p>
        )}
      </div>

      {error && <div className="error no-print">{error}</div>}

      {stats && (
        <div className="grid grid-3 no-print" style={{ margin: "1.25rem 0" }}>
          <div className="card">
            <p className="muted" style={{ margin: 0 }}>
              {t("dashboard.totalReports")}
            </p>
            <h2 style={{ margin: "0.25rem 0 0" }}>{stats.total_reports}</h2>
          </div>
          <div className="card">
            <p className="muted" style={{ margin: 0 }}>
              {t("dashboard.analyzed")}
            </p>
            <h2 style={{ margin: "0.25rem 0 0" }}>{stats.analyzed_reports}</h2>
          </div>
          <div className="card">
            <p className="muted" style={{ margin: 0 }}>
              {t("dashboard.chatMessages")}
            </p>
            <h2 style={{ margin: "0.25rem 0 0" }}>{stats.total_chat_messages}</h2>
          </div>
        </div>
      )}

      <div className="no-print" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
        <h2>{t("dashboard.recentReports")}</h2>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <Link to="/upload" className="btn">
            {t("dashboard.uploadReport")}
          </Link>
          <Link to="/batches/upload" className="btn btn-secondary" style={{ padding: "0.6rem 1rem" }}>
            {t("batch.upload.title")}
          </Link>
        </div>
      </div>

      {reports.length === 0 ? (
        <div className="card no-print">
          <p className="muted">{t("dashboard.noReports")}</p>
        </div>
      ) : (
        <div className="grid no-print">
          {reports.map((report) => (
            <ReportCard key={report.id} report={report} />
          ))}
        </div>
      )}

      <div className="print-only">
        <CompanyProfile settings={settings} printable />
      </div>
    </div>
  );
}
