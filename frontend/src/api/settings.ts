import { apiClient } from "./client";
import {
  emptyBilingual,
  type AppLanguage,
  type BilingualText,
  type CompanySettings,
  type UpdateCompanySettingsPayload,
} from "../utils/bilingual";

export type { BilingualText, CompanySettings, UpdateCompanySettingsPayload, AppLanguage };
export {
  emptyBilingual,
  hasBilingualContent,
  hasCompanyProfile,
  hasRequiredBranding,
  pickLocalized,
} from "../utils/bilingual";

export async function getCompanySettings(): Promise<CompanySettings> {
  return apiClient.request("/api/settings/company");
}

export async function updateCompanySettings(
  payload: UpdateCompanySettingsPayload
): Promise<CompanySettings> {
  return apiClient.request("/api/settings/company", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function uploadCompanyLogo(file: File): Promise<CompanySettings> {
  const form = new FormData();
  form.append("file", file);
  return apiClient.request("/api/settings/company/logo", {
    method: "POST",
    body: form,
  });
}

export async function deleteCompanyLogo(): Promise<CompanySettings> {
  return apiClient.request("/api/settings/company/logo", {
    method: "DELETE",
  });
}

export function companyLogoSrc(logoUrl: string | null): string | null {
  if (!logoUrl) return null;
  const base = import.meta.env.VITE_API_URL ?? "";
  return `${base}${logoUrl}`;
}

export const DEFAULT_COMPANY_SETTINGS: CompanySettings = {
  company_name: { ar: "جلفار", en: "Galfar" },
  page_title: {
    ar: "جلفار — محلل التقارير المالية",
    en: "Galfar — Financial Report Analyzer",
  },
  tagline: emptyBilingual(),
  logo_url: null,
  address: emptyBilingual(),
  industry: emptyBilingual(),
  history: emptyBilingual(),
  introduction_html: emptyBilingual(),
  phone: "",
  email: "",
  website: "",
  updated_at: null,
};
