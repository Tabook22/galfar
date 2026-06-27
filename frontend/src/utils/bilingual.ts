export interface BilingualText {
  ar: string;
  en: string;
}

export interface CompanySettings {
  company_name: BilingualText;
  page_title: BilingualText;
  tagline: BilingualText;
  logo_url: string | null;
  address: BilingualText;
  industry: BilingualText;
  history: BilingualText;
  introduction_html: BilingualText;
  phone: string;
  email: string;
  website: string;
  updated_at: string | null;
}

export type UpdateCompanySettingsPayload = Omit<
  CompanySettings,
  "logo_url" | "updated_at"
>;

export type AppLanguage = "en" | "ar";

export function emptyBilingual(): BilingualText {
  return { ar: "", en: "" };
}

export function pickLocalized(text: BilingualText, language: AppLanguage): string {
  const primary = language === "ar" ? text.ar : text.en;
  const fallback = language === "ar" ? text.en : text.ar;
  return (primary || fallback || "").trim();
}

export function hasBilingualContent(text: BilingualText): boolean {
  return Boolean(text.ar.trim() || text.en.trim());
}

export function hasCompanyProfile(settings: CompanySettings): boolean {
  return Boolean(
    hasBilingualContent(settings.tagline) ||
      hasBilingualContent(settings.address) ||
      hasBilingualContent(settings.industry) ||
      hasBilingualContent(settings.history) ||
      hasBilingualContent(settings.introduction_html) ||
      settings.phone ||
      settings.email ||
      settings.website
  );
}

export function hasRequiredBranding(settings: CompanySettings): boolean {
  return (
    hasBilingualContent(settings.company_name) && hasBilingualContent(settings.page_title)
  );
}
