import { Link, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { companyLogoSrc, pickLocalized } from "../api/settings";
import { useCompanyBranding } from "../context/CompanySettingsContext";
import LanguageSwitcher from "./LanguageSwitcher";

export default function Layout() {
  const { t, i18n } = useTranslation();
  const branding = useCompanyBranding();
  const logoSrc = companyLogoSrc(branding.logo_url);
  const lang = i18n.language === "ar" ? "ar" : "en";
  const companyName = pickLocalized(branding.company_name, lang) || t("app.name");

  return (
    <div>
      <header className="app-header no-print">
        <div className="container header-inner">
          <Link to="/" className="header-brand">
            {logoSrc && <img src={logoSrc} alt="" className="header-logo" />}
            <span>{companyName}</span>
          </Link>
          <nav className="header-nav">
            <Link to="/">{t("nav.dashboard")}</Link>
            <Link to="/batches">{t("nav.batches")}</Link>
            <Link to="/upload">{t("nav.upload")}</Link>
            <Link to="/reports">{t("nav.reports")}</Link>
            <Link to="/saved-analyses">{t("nav.savedAnalyses")}</Link>
            <Link to="/settings">{t("nav.settings")}</Link>
            <LanguageSwitcher />
          </nav>
        </div>
      </header>
      <main className="container">
        <Outlet />
      </main>
    </div>
  );
}
