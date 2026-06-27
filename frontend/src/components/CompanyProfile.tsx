import { memo, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import {
  companyLogoSrc,
  hasBilingualContent,
  hasCompanyProfile,
  pickLocalized,
  type AppLanguage,
  type CompanySettings,
} from "../api/settings";
import RichTextContent from "./RichTextContent";

interface Props {
  settings: CompanySettings;
  printable?: boolean;
  showEmptyHint?: boolean;
  language?: AppLanguage;
}

function ProfileBlock({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="company-profile-block">
      <h3>{title}</h3>
      {children}
    </div>
  );
}

function LocalizedProfileContent({
  settings,
  language,
  t,
}: {
  settings: CompanySettings;
  language: AppLanguage;
  t: (key: string) => string;
}) {
  const companyName = pickLocalized(settings.company_name, language);
  const tagline = pickLocalized(settings.tagline, language);
  const industry = pickLocalized(settings.industry, language);
  const address = pickLocalized(settings.address, language);
  const history = pickLocalized(settings.history, language);
  const introduction = pickLocalized(settings.introduction_html, language);

  return (
    <>
      <div className="company-profile-header">
        <div>
          <h2 className="company-profile-name">{companyName}</h2>
          {tagline && <p className="company-profile-tagline">{tagline}</p>}
        </div>
      </div>
      <div className="company-profile-details">
        {industry && (
          <p>
            <strong>{t("settings.industry")}:</strong> {industry}
          </p>
        )}
        {address && (
          <p>
            <strong>{t("settings.address")}:</strong> {address}
          </p>
        )}
        {(settings.phone || settings.email || settings.website) && (
          <p className="company-profile-contact">
            {settings.phone && (
              <span>
                <strong>{t("settings.phone")}:</strong> {settings.phone}
              </span>
            )}
            {settings.email && (
              <span>
                <strong>{t("settings.email")}:</strong> {settings.email}
              </span>
            )}
            {settings.website && (
              <span>
                <strong>{t("settings.website")}:</strong> {settings.website}
              </span>
            )}
          </p>
        )}
        {history && (
          <ProfileBlock title={t("settings.history")}>
            <p className="company-profile-text">{history}</p>
          </ProfileBlock>
        )}
        {introduction && (
          <ProfileBlock title={t("settings.introduction")}>
            <RichTextContent value={introduction} />
          </ProfileBlock>
        )}
      </div>
    </>
  );
}

function CompanyProfile({
  settings,
  printable = false,
  showEmptyHint = false,
  language,
}: Props) {
  const { t, i18n } = useTranslation();
  const logoSrc = companyLogoSrc(settings.logo_url);
  const hasProfile = hasCompanyProfile(settings);
  const activeLang: AppLanguage = language ?? (i18n.language === "ar" ? "ar" : "en");

  if (!hasProfile && !logoSrc && !showEmptyHint) {
    return null;
  }

  const showBoth = printable;

  return (
    <section
      className={`company-profile${printable ? " company-profile-printable" : ""}`}
      id={printable ? "company-profile-print" : undefined}
    >
      {logoSrc && (
        <div className="company-profile-logo-wrap">
          <img
            src={logoSrc}
            alt={pickLocalized(settings.company_name, activeLang)}
            className="company-profile-logo"
          />
        </div>
      )}

      {!hasProfile && showEmptyHint ? (
        <p className="muted">{t("settings.profileEmptyHint")}</p>
      ) : showBoth ? (
        <div className="company-profile-bilingual">
          {(hasBilingualContent(settings.company_name) ||
            settings.tagline.en ||
            settings.industry.en ||
            settings.address.en ||
            settings.history.en ||
            settings.introduction_html.en) && (
            <div className="company-profile-lang-block" dir="ltr" lang="en">
              <h3 className="company-profile-lang-title">{t("language.en")}</h3>
              <LocalizedProfileContent settings={settings} language="en" t={t} />
            </div>
          )}
          {(settings.company_name.ar ||
            settings.tagline.ar ||
            settings.industry.ar ||
            settings.address.ar ||
            settings.history.ar ||
            settings.introduction_html.ar) && (
            <div className="company-profile-lang-block" dir="rtl" lang="ar">
              <h3 className="company-profile-lang-title">{t("language.ar")}</h3>
              <LocalizedProfileContent settings={settings} language="ar" t={t} />
            </div>
          )}
        </div>
      ) : (
        <LocalizedProfileContent settings={settings} language={activeLang} t={t} />
      )}
    </section>
  );
}

export default memo(CompanyProfile);
